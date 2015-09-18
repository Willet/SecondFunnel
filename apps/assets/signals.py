import json

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
    """Generate cache for IR tiles if related products or content changed."""
    if (sender is Content.tagged_products.through or
            sender is Product.similar_products.through) and \
            kwargs.get('action') in ('post_add', 'post_clear', 'post_remove') and \
            len(kwargs.get('pk_set')) > 0:
        # populate set of objects whose tiles need to be refreshed
        instances = []
        if kwargs.get('reverse'):
            # update tiles of other side of m2m relationship
            for pk in kwargs.get('pk_set'):
                inst = kwargs.get('model').objects.get(pk=pk)
                instances.append(inst)
        else:
            instance = kwargs.pop('instance', None)
            instances.append(instance)

        for inst in instances:
            for tile in inst.tiles.all():
                # validation can be skipped because 
                # only product/content relationships are changed
                ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
                if updated:
                    post_save.disconnect(tile_saved, sender=Tile)
                    models.Model.save(tile, update_fields=['ir_cache'])
                    post_save.connect(tile_saved, sender=Tile)


@receiver(post_save, sender=Tile)
def tile_saved(sender, **kwargs):
    """Generate cache for IR tiles if it was change."""
    tile = kwargs.pop('instance', None)
    if not tile:
        return

    ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
    if updated:
        post_save.disconnect(tile_saved, sender=Tile)
        models.Model.save(tile, update_fields=['ir_cache']) # skip full_clean
        post_save.connect(tile_saved, sender=Tile)
