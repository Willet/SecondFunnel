import sys

from contextlib2 import ContextDecorator
from django.db.models.signals import post_save, m2m_changed


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

    def __enter__(self):
        self.disabled_counter += 1
        try:
            disable_tile_serialization_signals()
        except:
            # If disconnecting signals failed for any reason
            # re-connect signals if no wrapping context managers and re-raise
            try:
                self.__exit__(*sys.exc_info())
            except:
                # Suppress any additional exception from __exit__
                pass
            raise

    def __exit__(self, type, value, traceback):
        self.disabled_counter -= 1
        if self.disabled_counter < 1:
            enable_tile_serialization_signals()
            # Should never have exit'ed more than enter'ed.
            assert self.disabled_counter == 0


class TileSerializationQueue(object):
    """
    Queue's tiles for serialization by intercepting signals that would trigger tile seriailzation

    In use, `start`, `stop` then `serialize`
    """
    def __init__(self):
        self.tiles_to_serialize = set()

    def _record_tile_save(self, sender, **kwargs):
        import apps.assets.models as models

        tile = kwargs.pop('instance', None)
        if isinstance(tile, models.Tile):
            self.tiles_to_serialize.add(tile.pk)

    def _record_m2m_save(self, sender, **kwargs):
        import apps.assets.models as models

        added_or_removed_keys = kwargs.get('pk_set') or [] # for some signals, pk_set is None
    
        if (sender in [models.Content.tagged_products.through, models.Product.similar_products.through]) \
                and kwargs.get('action') in ('post_add', 'post_clear', 'post_remove') \
                and len(added_or_removed_keys) > 0:
            # populate set of objects whose tiles need to be refreshed
            instances = []
            if kwargs.get('reverse'):
                # update tiles of other side of m2m relationship
                for pk in added_or_removed_keys:
                    inst = kwargs.get('model').objects.get(pk=pk)
                    instances.append(inst)
            else:
                instance = kwargs.pop('instance', None)
                instances.append(instance)

            for inst in instances:
                for tile in inst.tiles.all():
                    self.tiles_to_serialize.add(tile.pk)

        elif (sender in [models.Tile.products.through, models.Tile.content.through]) \
                and kwargs.get('action') in ('post_add', 'post_clear', 'post_remove') \
                and len(added_or_removed_keys) > 0:
            # populate set of objects whose tiles need to be refreshed
            tiles = []
            if kwargs.get('reverse'):
                # update tiles of other side of m2m relationship
                for pk in added_or_removed_keys:
                    tile = kwargs.get('model').objects.get(pk=pk)
                    tiles.append(tile)
            else:
                tile = kwargs.pop('instance', None)
                tiles.append(tile)

            for tile in tiles:
                self.tiles_to_serialize(tile.pk)

    def start(self):
        import apps.assets.models as models

        disable_tile_serialization_signals()
        post_save.connect(self._record_tile_saved, sender=models.Tile)
        m2m_changed.connect(self._record_m2m_changed)

    def stop(self):
        import apps.assets.models as models

        post_save.disconnect(receiver=self._record_tile_saved, sender=models.Tile)
        m2m_changed.disconnect(self._record_m2m_changed)
        enable_tile_serialization_signals()

    def serialize(self):
        import apps.assets.models as models
        post_save.disconnect(tile_saved, sender=models.Tile)

        for tile in Tile.objects.get(pk__in=self.tiles_to_serialize)
            ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
            logging.debug("tile_saved {}".format(ir_cache))
            if updated:
                models.Model.save(tile, update_fields=['ir_cache']) # skip full_clean

        post_save.connect(tile_saved, sender=Tile)


def queue_tile_serialization(ContextDecorator):
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

    def __enter__(self):
        self.disabled_counter += 1
        try:
            self.queue.start()
        except:
            # If disconnecting signals failed for any reason
            # re-connect signals if no wrapping context managers and re-raise
            try:
                self.__exit__(*sys.exc_info())
            except:
                # Suppress any additional exception from __exit__
                pass
            raise

    def __exit__(self, type, value, traceback):
        self.disabled_counter -= 1
        if self.disabled_counter < 1:
            self.queue.stop()
            self.queue.serialize_tiles()
            # Should never have exit'ed more than enter'ed.
            assert self.disabled_counter == 0
