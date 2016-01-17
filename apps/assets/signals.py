import json
import logging

from django.db import models, transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from apps.assets.models import Tile, Product, Content, ProductImage

@receiver(post_save, sender=ProductImage)
def productimage_saved(sender, **kwargs):
    """Generate cache for IR tiles if a product is saved."""
    productimage = kwargs.pop('instance', None)
    if not (productimage and productimage.product):
        return

    productimage.product.save()


@receiver(post_save, sender=Product)
def product_saved(sender, **kwargs):
    """Generate cache for IR tiles if a product is saved."""
    product = kwargs.pop('instance', None)
    if not product:
        return

    with transaction.atomic():
        for tile in product.tiles.all():
            tile.save()


@receiver(post_save)
def content_saved(sender, **kwargs):
    """Generate cache for IR tiles if a content is saved."""

    content = kwargs.pop('instance', None)
    if not isinstance(content, Content):
        return

    with transaction.atomic():
        for tile in content.tiles.all():
            tile.save()


@receiver(m2m_changed)
def content_m2m_changed(sender, **kwargs):
    """Re-generate cache for IR tiles if contained product or content has its 
       related products changed
       ex: Tile -> Content -> tagged products updated
           Tile -> Product -> similar products updated
    """
    if sender in [Content.tagged_products.through, Product.similar_products.through]:
        logging.debug('content_m2m_changed {} {} {}'.format(kwargs.get('action'), sender, kwargs.get('reverse')))
        
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
                if sender == Content.tagged_products.through:
                    instances = instance.content.all()
                elif sender == Product.similar_products.through:
                    instances = instance.reverse_similar_products.all()
            else:
                instances.append(instance)

        for inst in instances:
            for tile in inst.tiles.all():
                # validation can be skipped because 
                # only 2nd order product/content relationships are changed
                ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
                logging.debug("\ttile updated: {}".format(ir_cache))
                if updated:
                    post_save.disconnect(tile_saved, sender=Tile)
                    models.Model.save(tile, update_fields=['ir_cache', 'placeholder'])
                    post_save.connect(tile_saved, sender=Tile)


@receiver(m2m_changed)
def tile_m2m_changed(sender, **kwargs):
    """Re-generate cache for IR tiles if products or content changed on tile."""
    if sender in [Tile.products.through, Tile.content.through]:
        logging.debug('tile_m2m_changed {} {} {}'.format(kwargs.get('action'), sender, kwargs.get('reverse')))

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
            # must validate
            ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
            logging.debug("\ttile updated: {}".format(ir_cache))
            if updated:
                post_save.disconnect(tile_saved, sender=Tile)
                tile.save() # run full clean before saving ir cache
                post_save.connect(tile_saved, sender=Tile)


@receiver(post_save, sender=Tile)
def tile_saved(sender, **kwargs):
    """Generate cache for IR tiles if it was change."""
    tile = kwargs.pop('instance', None)
    if not tile:
        return

    ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
    logging.debug("tile_saved {}".format(ir_cache))
    if updated:
        post_save.disconnect(tile_saved, sender=Tile)
        models.Model.save(tile, update_fields=['ir_cache', 'placeholder']) # skip full_clean
        post_save.connect(tile_saved, sender=Tile)
