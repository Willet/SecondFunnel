# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from django.core.exceptions import ValidationError
from scrapy.contrib.djangoitem import DjangoItem
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from apps.assets.models import Store
from apps.scraper.scrapers import ProductScraper
from apps.scrapy.items import ScraperProduct, ScraperContent
from apps.scrapy.utils import CloudinaryStore, spider_pipelined, \
    item_to_model, get_or_create, update_model


class CloudinaryPipeline(ImagesPipeline):
    """
    Enable Cloudinary storage using the ImagePipeline.

    Highly experimental, as ImagePipeline isn't really extensible at the
    moment.

    More details on the Image Pipeline here:
        http://doc.scrapy.org/en/latest/topics/images.html
    """
    def _get_store(self, uri):
        return CloudinaryStore()


class PricePipeline(object):
    @spider_pipelined
    def process_item(self, item, spider):
        item['price'] = item.get('price', '').strip()

        if item['price'].startswith('$'):
            item['price'] = item['price'][1:]

        item['price'] = int(float(item['price']))
        return item


# At the moment, ForeignKeys are a bitch, so, handle those separately.
class ProductForeignKeyPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
            return self.process_product(item, spider)

        elif isinstance(item, ScraperContent):
            return self.process_content(item, spider)

        return item

    def process_product(self, item, spider):
        store_slug = getattr(spider, 'store_slug', '')

        try:
            store = Store.objects.get(slug=store_slug)
        except Store.DoesNotExist:
            raise DropItem("Can't add item to non-existent store")

        item['store'] = store

        return item

    def process_content(self, item, spider):
        return item


# Any changes to the item after this pipeline will not be persisted.
# It is suggested that this be the last pipeline
class ItemPersistencePipeline(object):
    def process_item(self, item, spider):
        try:
            item_model = item_to_model(item)
        except TypeError:
            return item

        model, created = get_or_create(item_model)

        try:
            update_model(model, item)
        except ValidationError as e:
            messages = ','.join(e.messages)
            raise DropItem('Item didn\'t validate. ({})'.format(messages))

        return item


class ProductImagePipeline(object):
    def process_item(self, item, spider):
        for image_url in item.get('image_urls', []):
            self.process_image(item, image_url)

        return item

    def process_image(self, item, image_url):
        store = item['store']
        product = item['sku']
        ProductScraper.process_image(image_url, product, store)
