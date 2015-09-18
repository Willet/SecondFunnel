import json

from celery import Celery       
from celery.utils.log import get_task_logger
from django.db import models, transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from apps.assets.models import Tile, Product, Content, ProductImage

celery = Celery()
logger = get_task_logger(__name__)


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
    """Generate cache for IR tiles if it was change.

    TODO: this is CPU-intensive. How can tile freshness be checked without
          first computing the updated cache?
    """
    instance = kwargs.pop('instance', None)
    actionable = kwargs.get('action') in ('post_add', 'post_clear', 'post_remove')

    if not (type(sender) is type(Content.tagged_products.through) or
            type(sender) is type(Product.similar_products.through)):
        return

    if not actionable:
        return

    with transaction.atomic():
        for tile in instance.tiles.all():
            tile.save()


@receiver(post_save, sender=Tile)
def tile_saved(sender, **kwargs):
    """Generate cache for IR tiles if it was change.

    TODO: this is CPU-intensive. How can tile freshness be checked without
          first computing the updated cache?
    """
    tile = kwargs.pop('instance', None)
    if not tile:
        return

    ir_cache, updated = tile.update_ir_cache() # sets tile.ir_cache
    if updated:
        post_save.disconnect(tile_saved, sender=Tile)
        models.Model.save(tile, update_fields=['ir_cache']) # skip full_clean
        post_save.connect(tile_saved, sender=Tile)
