# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from apps.assets.models import Store
from apps.scrapy.items import ScraperProduct
from apps.scrapy.utils import CloudinaryStore, spider_pipelined, \
    item_to_model, get_or_create, update_model


class CloudinaryPipeline(ImagesPipeline):
    """
    Try to hook into the existing ImagesPipeline making as few changes as
    possible.
    """
    def _get_store(self, uri):
        return CloudinaryStore()

    def image_downloaded(self, response, request, info):
        """
        Store the downloaded image and return the checksum.

        Called after the file has been downloaded locally.
        """
        return super(CloudinaryPipeline, self).image_downloaded(
            response, request, info
        )

    def get_images(self, response, request, info):
        """
        Obtains a list of path, image, and buffer tuples
        """
        return super(CloudinaryPipeline, self).get_images(
            response, request, info
        )

    def convert_image(self, image, size=None):
        """
        Standardizes images
        """
        return super(CloudinaryPipeline, self).convert_image(image, size)


class PricePipeline(object):
    @spider_pipelined
    def process_item(self, item, spider):
        item['price'] = item['price'].strip()

        if item['price'].startswith('$'):
            item['price'] = item['price'][1:]

        item['price'] = int(float(item['price']))
        return item

# At the moment, ForeignKeys are a bitch, so, handle those separately.
class ProductForeignKeyPipeline(object):
    def process_item(self, item, spider):
        if not isinstance(item, ScraperProduct):
            return item

        store_slug = getattr(spider, 'store_slug', '')

        try:
            store = Store.objects.get(slug=store_slug)
        except Store.DoesNotExist:
            raise DropItem("Can't add item to non-existent store")

        item['store'] = store
        return item

# This must be the last thing that we to the item
# Why? Because after we persist to the database, it doesn't matter
# What changes we make to the item.
class ItemPersistencePipeline(object):
    def process_item(self, item, spider):
        try:
            item_model = item_to_model(item)
        except TypeError:
            return item

        model, created = get_or_create(item_model)

        update_model(model, item)

        return item
