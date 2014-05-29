# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from collections import defaultdict
from django.core.exceptions import ValidationError
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from apps.assets.models import Store, Product, Category
from apps.scraper.scrapers import ProductScraper
from apps.scrapy.items import ScraperProduct, ScraperContent
from apps.scrapy.utils.django import item_to_model, get_or_create, update_model
from apps.scrapy.utils.misc import CloudinaryStore, spider_pipelined


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


# TODO: Many of these pipelines could likely be processors instead


class NamePipeline(object):
    @spider_pipelined
    def process_item(self, item, spider):
        return item


class ValidationPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
            return self.process_product(item, spider)

        elif isinstance(item, ScraperContent):
            return self.process_content(item, spider)

        return item

    def process_product(self, item, spider):
        # Drop items missing required fields
        required = ['sku', 'name']
        empty_fields = [k for (k,v) in item.items() if not v and k in required]
        if empty_fields:
            msg = 'Product fields cannot be blank: ({})'.format(
                ', '.join(empty_fields)
            )
            raise DropItem(msg)

        return item

    def process_content(self, item, spider):
        pass


class PricePipeline(object):
    @spider_pipelined
    def process_item(self, item, spider):
        item['price'] = item.get('price', '').strip()

        # TODO: Maybe have default currency options in options?
        currency_info = getattr(spider, 'currency_info', {})
        symbol = currency_info.get('symbol', '$')
        position_at_end = currency_info.get('position-at-end')

        item['price'] = item['price'].strip(symbol)
        item['price'] = float(item['price'])

        # Our Product model uses a narrow regex...
        # So, forget all this fanciness until that is changed.

        # if position_at_end:
        #     template = u'{price}{symbol}'
        # else:
        #     template = u'{symbol}{price}'

        # item['price'] = template.format(price=item['price'], symbol=symbol)
        item['price'] = u'{symbol}{price}'.format(
            price=item['price'], symbol=symbol
        )

        return item


class DuplicatesPipeline(object):
    """
    Detects if there are duplicates based on sku and spider name.

    Alternatively, we could do some sort of merge if there are duplicates...
    """
    def __init__(self):
        self.ids_seen = defaultdict(set)

    def process_item(self, item, spider):
        spider_name = spider.name
        sku = item['sku']

        if sku in self.ids_seen[spider_name]:
            raise DropItem("Duplicate item found: {}".format(item))

        self.ids_seen[spider_name].add(sku)
        return item


# At the moment, ForeignKeys are a bitch, so, handle those separately.
class ForeignKeyPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
            return self.process_product(item, spider)

        elif isinstance(item, ScraperContent):
            return self.process_content(item, spider)

        return item

    def process_product(self, item, spider):
        item = self.associate_store(item, spider)

        return item

    def associate_store(self, item, spider):
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


class CategoryPipeline(object):
    def process_item(self, item, spider):
        categories = item.get('attributes', {}).get('categories', [])
        for name, url in categories:
            self.add_to_category(item, name, url)

        return item

    def add_to_category(self, item, name, url=None):
        kwargs = {
            'store': item['store'],
            'name': name
        }

        if url:
            kwargs['url'] = url

        category, created = Category.objects.get_or_create(**kwargs)
        category.save()

        try:
            item_model = item_to_model(item)
        except TypeError:
            return

        product, _ = get_or_create(item_model)
        category.products.add(product)
        category.save()


class ProductImagePipeline(object):
    def process_item(self, item, spider):
        for image_url in item.get('image_urls', []):
            self.process_image(item, image_url)

        return item

    def process_image(self, item, image_url):
        store = item['store']
        product = item['sku']
        try:
            ProductScraper.process_image(image_url, product, store)
        except Product.MultipleObjectsReturned:
            raise DropItem(
                'Unclear which product to attach to image. '\
                'More than one product (sku: "{}", store: "{}")'.format(
                    product, store.id
                )
            )
