# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from collections import defaultdict
from django.core.exceptions import ValidationError
from scrapy.exceptions import DropItem
from apps.assets.models import Store, Product, Content, Category, Feed
from apps.scraper.scrapers import ProductScraper, ContentScraper
from apps.scrapy.items import ScraperProduct, ScraperContent, ScraperImage
from apps.scrapy.utils.django import item_to_model, get_or_create, update_model
from scrapy.contrib.djangoitem import DjangoItem

# TODO: Many of these pipelines could likely be processors instead


class ValidationPipeline(object):
    """
    Determine if there is validation errors if we were to save the model
    so far.
    """
    def process_item(self, item, spider):
        if isinstance(item, DjangoItem):
            try:
                django_model = item.save(commit=False)
                django_model.full_clean()
            except ValidationError as e:
                raise DropItem("DjangoItem didn\'t validate. ({})".format(e))
        return item


class DuplicatesPipeline(object):
    """
    Detects if there are duplicates based on uniqueness of items
    from the same spider.
    """
    def __init__(self):
        self.ids_seen = defaultdict(list)

    def process_item(self, item, spider):
        # TODO: this assumes only one model type which could be
        #       a bad assumption if the uniqueness dict's are the same
        #
        # e.g. two different item-types that have same uniqueness constraint
        #      will still collide
        spider_name = spider.name
        uniqueness = getattr(item, 'uniqueness', ())
        for uniq_attributes in uniqueness:
            lookup_dict = {}
            for attr in uniq_attributes:
                if attr in item:
                    lookup_dict[attr] = item.get(attr)
                else:
                    # if no attribute, it can't provide uniqueness
                    continue

            if lookup_dict in self.ids_seen[spider_name]:
                raise DropItem("Duplicate item found: {}".format(item))

            self.ids_seen[spider_name].append(lookup_dict)

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

    def process_content(self, item, spider):
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


# Any changes to the item after this pipeline will not be persisted.
# It is suggested that this be the last pipeline
class ItemPersistencePipeline(object):
    def process_item(self, item, spider):
        model, created = get_or_create(item)

        try:
            update_model(model, item)
        except ValidationError as e:
            # This happens when the merged model does not validate
            raise DropItem('Item didn\'t validate on save. ({})'.format(e))

        return item


class CategoryPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
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


class FeedPipeline(object):
    def process_item(self, item, spider):
        feed_ids = getattr(spider, 'feed_ids', [])

        for feed_id in feed_ids:
            self.add_to_feed(item, feed_id)

        return item

    def add_to_feed(self, item, feed_id):
        try:
            feed = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            return

        try:
            item_model = item_to_model(item)
        except TypeError:
            return

        if isinstance(item_model, Product):
            feed.add_product(product=item_model)
        elif isinstance(item_model, Content):
            feed.add_content(content=item_model)


class ProductImagePipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
            for image_url in item.get('image_urls', []):
                self.process_product_image(item, image_url)
        return item

    def process_product_image(self, item, image_url):
        store = item['store']
        product = item['sku']
        try:
            ProductScraper.process_image(image_url, product, store)
        except Product.MultipleObjectsReturned:
            raise DropItem(
                'Unclear which product to attach to image. '
                'More than one product (sku: "{}", store: "{}")'.format(
                    product, store.id
                )
            )


class ContentImagePipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperImage):
            if item.get('source_url', False):
                item = ContentScraper.process_image(item['source_url'], item, item['store'])
        return item
