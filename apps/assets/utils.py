from contextlib2 import ContextDecorator
from django.db import models as django_models
from django.db.models.signals import post_save, m2m_changed
import logging
import sys


def disable_tile_serialization_signals():
    """ Disconnects all assets signals that trigger tile serialization """
    # lazy load circular import (signals.py -> models.py -> utils.py -> signals.py)
    import apps.assets.signals as signals
    import apps.assets.models as models

    post_save.disconnect(receiver=signals.tile_saved, sender=models.Tile)
    m2m_changed.disconnect(signals.tile_m2m_changed)
    m2m_changed.disconnect(signals.content_m2m_changed)

def enable_tile_serialization_signals():
    """ Connects all assets signals that trigger tile serialization """
    # lazy load circular import (signals.py -> models.py -> utils.py -> signals.py)
    import apps.assets.signals as signals
    import apps.assets.models as models

    post_save.connect(signals.tile_saved, sender=models.Tile)
    m2m_changed.connect(signals.tile_m2m_changed)
    m2m_changed.connect(signals.content_m2m_changed)


class disable_tile_serialization(ContextDecorator):
    """ Context manager that suppresses tile serialization until exit
        
        Useful when creating a new tile that requires multiple steps before serializing
            ex: adding multiple different m2m keys

        Can safely be nested
    """
    # Avoid pre-maturally re-enabling signals if this context manager is nested
    # Keep track of how many times this has been entered
    disabled_counter = 0

    @classmethod
    def __enter__(cls):
        cls.disabled_counter += 1
        try:
            disable_tile_serialization_signals()
        except:
            # If disconnecting signals failed for any reason
            # re-connect signals if no wrapping context managers and re-raise
            try:
                cls.__exit__(*sys.exc_info())
            except:
                # Suppress any additional exception from __exit__
                pass
            raise

    @classmethod
    def __exit__(cls, type, value, traceback):
        cls.disabled_counter -= 1
        if cls.disabled_counter < 1:
            enable_tile_serialization_signals()
            # Should never have exit'ed more than enter'ed.
            assert cls.disabled_counter == 0


class TileSerializationQueue(object):
    """
    Queue's tiles for serialization by intercepting signals that would trigger tile seriailzation

    To use, `start`, `stop` then `serialize`
    """
    def __init__(self):
        self.tiles_to_serialize = set()

    def __len__(self):
        return len(self.tiles_to_serialize)

    def _record_tile_save(self, sender, **kwargs):
        import apps.assets.models as models

        tile = kwargs.pop('instance', None)
        if isinstance(tile, models.Tile):
            self.tiles_to_serialize.add(tile.pk)

    def _record_m2m_changed(self, sender, **kwargs):
        import apps.assets.models as models
    
        if sender in [models.Content.tagged_products.through, models.Product.similar_products.through]:
            instances = []
            added_or_removed_keys = kwargs.get('pk_set') or [] # for some signals, pk_set is None

            if (kwargs.get('action') in ('post_add', 'post_remove')) and (len(added_or_removed_keys) > 0):
                # populate set of objects whose tiles need to be refreshed
                if kwargs.get('reverse'):
                    # update tiles of other side of m2m relationship
                    for pk in added_or_removed_keys:
                        inst = kwargs.get('model').objects.get(pk=pk)
                        instances.append(inst)
                else:
                    instance = kwargs.pop('instance', None)
                    instances.append(instance)

            # clear does not provide a pk_set, so must use relation pre_clear
            elif kwargs.get('action') == 'pre_clear':
                instance = kwargs.pop('instance', None)
                if kwargs.get('reverse'):
                    if sender == models.Content.tagged_products.through:
                        instances = instance.content.all()
                    elif sender == models.Product.similar_products.through:
                        instances = instance.reverse_similar_products.all()
                else:
                    instances.append(instance)

            for inst in instances:
                for tile in inst.tiles.all():
                    self.tiles_to_serialize.add(tile.pk)

        elif sender in [models.Tile.products.through, models.Tile.content.through]:
            tiles = []
            added_or_removed_keys = kwargs.get('pk_set') or [] # for some signals, pk_set is None

            if (kwargs.get('action') in ('post_add', 'post_remove')) and (len(added_or_removed_keys) > 0):
                # populate set of objects whose tiles need to be refreshed
                if kwargs.get('reverse'):
                    # update tiles of other side of m2m relationship
                    for pk in added_or_removed_keys:
                        tile = kwargs.get('model').objects.get(pk=pk)
                        tiles.append(tile)
                else:
                    tile = kwargs.pop('instance', None)
                    tiles.append(tile)

            # clear does not provide a pk_set, so must use relation pre_clear
            elif kwargs.get('action') == 'pre_clear':
                instance = kwargs.pop('instance', None)
                if kwargs.get('reverse'):
                    tiles = instance.tiles.all() # reverse relation for both product and content is tiles
                else:
                    tiles.append(instance)

            for tile in tiles:
                self.tiles_to_serialize.add(tile.pk)

    def add(self, tile_or_tiles):
        """
        Add tile or tiles to queue.
        """
        import apps.assets.models as models

        if isinstance(tile_or_tiles, models.Tile):
            self.tiles_to_serialize.add(tile_or_tiles.pk)
        else:
            for t in tile_or_tiles:
                if isinstance(t, models.Tile):
                    self.tiles_to_serialize.add(t.pk)
                else:
                    raise TypeError(u"{} is not a Tile instance".format(t))

    def start(self):
        """
        Start queuing of tiles to serialize
        """
        import apps.assets.models as models

        disable_tile_serialization_signals()
        post_save.connect(self._record_tile_save, sender=models.Tile)
        m2m_changed.connect(self._record_m2m_changed)

    def stop(self):
        """
        Stop queuing of tiles to serialize
        """
        import apps.assets.models as models

        post_save.disconnect(receiver=self._record_tile_save, sender=models.Tile)
        m2m_changed.disconnect(self._record_m2m_changed)
        enable_tile_serialization_signals()

    def serialize(self):
        """
        Serialize all tiles in queue
        """
        import apps.assets.models as models

        tiles = models.Tile.objects.filter(pk__in=self.tiles_to_serialize)
        logging.debug("Serializing {} delayed tiles".format(tiles.count()))

        for tile in tiles.iterator():
            ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
            if updated:
                # TODO: convert to a bulk save operation for MASSIVE speedup
                django_models.Model.save(tile, update_fields=['ir_cache', 'placeholder']) # skip full_clean

        self.tiles_to_serialize = set() # reset queue


class delay_tile_serialization(ContextDecorator):
    """ Context manager that queues tile serialization until exit
        
        Useful when performing many operations that can trigger repeat serializations
        on the same tiles
            ex: updating a lot of products
        
        Can safely be nested
    """
    # Avoid pre-maturally re-enabling signals if this context manager is nested
    # Keep track of how many times this has been entered
    disabled_counter = 0
    queue = TileSerializationQueue()

    @classmethod
    def __enter__(cls):
        cls.disabled_counter += 1
        try:
            cls.queue.start()
        except:
            # If disconnecting signals failed for any reason
            # re-connect signals if no wrapping context managers and re-raise
            try:
                cls.__exit__(*sys.exc_info())
            except:
                # Suppress any additional exception from __exit__
                pass
            raise

    @classmethod
    def __exit__(cls, type, value, traceback):
        cls.disabled_counter -= 1
        if cls.disabled_counter < 1:
            cls.queue.stop()
            cls.queue.serialize()
            # Should never have exit'ed more than enter'ed.
            assert cls.disabled_counter == 0
