from django.core.exceptions import MultipleObjectsReturned
from django.db import transaction
from itertools import chain
from scrapy.exceptions import CloseSpider

from apps.assets.models import Category, Content, Feed, Product
from apps.assets.utils import disable_tile_serialization
from apps.intentrank.serializers import SerializerError
from apps.scrapy.items import ScraperProduct, ScraperContent, ScraperImage
from apps.scrapy.models import PlaceholderProduct

from .utils import SimpleModelCache


category_cache = SimpleModelCache(Category)
content_cache = SimpleModelCache(Content)
product_cache = SimpleModelCache(Product)


class AssociateMixin(object):
    """
    If a content has 'tag_with_products' field True and a 'content_id' field
    then tag with any subsequent products with 'content_id_to_tag' field matching
    'content_id'

    If a product has 'tag_with_products' field True and a 'product_id' field
    then tag with any subsequent products with 'product_id_to_tag' field matching
    'product_id'
    """
    def __init__(self, *args, **kwargs):
        # Shared cache accessible via any Pipeline
        self.images = content_cache
        self.products = product_cache
        super(AssociateMixin, self).__init__(*args, **kwargs)

    def store_content_to_tag(self, item, spider):
        """
        Cache content for tagging

        Item must have 'instance' and 'content_id'
        """
        self.images.add(item['instance'], item.get('content_id'), item['store'])

    def store_product_to_tag(self, item, spider):
        """
        Cache product for tagging

        Item must have 'instance' and 'product_id'
        """
        self.products.add(item['instance'], item.get('product_id'), item['store'])

    def tag_to_content(self, item, spider):
        """
        Tags this item to content

        Item must have 'instance' and 'content_id_to_tag'
        """
        product = item['instance']
        content_id = item.get('content_id_to_tag')
        image = self.images.get(content_id, item['store'])
        if image:
            tagged_product_ids = image.tagged_products.values_list('id', flat=True)
            if not product.id in tagged_product_ids:
                spider.logger.info(u"Tagging <Image {}> with <Product {}>".format(image.id, product.id))
                image.tagged_products.add(product)
            else:
                spider.logger.info(u"<Image {}> already tagged with <Product {}>".format(image.id, product.id))
        else:
            spider.logger.warning(u"Tried to tag <Product {}> to content_id {},\
                                    but it doesn't exist".format(product.id, content_id))

    def tag_to_product(self, item, spider):
        """
        Tags this item to product

        Item must have 'instance' and 'product_id_to_tag'
        """
        similar_product = item['instance']
        product_id = item.get('product_id_to_tag')
        product = self.products.get(product_id, item['store'])
        if product:
            similar_product_ids = product.similar_products.values_list('id', flat=True)
            if not similar_product.id in similar_product_ids:
                spider.logger.info(u"Tagging <Product {}> with <Product {}>".format(product.id,
                                                                                    similar_product.id))
                product.similar_products.add(similar_product)
            else:
                spider.logger.info(u"<Product {}> already tagged with <Product {}>".format(product.id,
                                                                                           similar_product.id))
        else:
            spider.logger.warning(u"Tried to tag <Product {}> to product_id {},\
                                    but it doesn't exist".format(similar_product.id, product_id))

    def persist_tagged_items(self, spider):
        """
        Save images and products in one transaction
        """
        with transaction.atomic():
            for instance in chain(self.images.dump_items(), self.products.dump_items()):
                instance.save()
        spider.logger.info(u'Saved {} tagged images and {} tagged products'.format(len(self.images),
                                                                                   len(self.products)))


class ItemManifold(object):
    """
    A Scrapy Pipeline that processes by scraper item type
    Pipeline is skipped if processor is not implemented for a type
    Has an optional default catch-all

    Supported items:

    ScraperProduct -> process_product
    ScraperContent -> process_content
    ScraperImage   -> process_image
    *              -> process_default
    """
    def __init__(self, *args, **kwargs):
        super(ItemManifold, self).__init__(*args, **kwargs)

    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
            return (self.process_product(item, spider) or item) if \
                callable(getattr(self.__class__, 'process_product', None)) else item
        elif isinstance(item, ScraperContent):
            return (self.process_content(item, spider) or item) if \
                callable(getattr(self.__class__, 'process_content', None)) else item
        elif isinstance(item, ScraperImage):
            return (self.process_image(item, spider) or item) if \
                callable(getattr(self.__class__, 'process_image', None)) else item
        elif callable(getattr(self.__class__, 'process_default', None)):
            return (self.process_default(item, spider) or item)
        else:
            return item


class PlaceholderMixin(object):
    """
    Adds methods to manage placeholder products
    """
    def __init__(self, *args, **kwargs):
        super(PlaceholderMixin, self).__init__(*args, **kwargs)

    def update_or_save_placeholder(self, item, spider):
        """ When a product is invalid for any reason:

        if it exists, set it to out of stock
        if it is a duplicate, merge and set to out of stock
        if it doesn't exist, create a placeholder

        Returns (<Product>, <Boolean> created)
        """
        url = item['url']
        store = item['store']
        sku = item.get('sku', None)

        try:
            product = Product.objects.get(url=url, store=store)
            product.in_stock = False
            try:
                product.save()
            except SerializerError as e:
                spider.logger.info("Converting {} to placeholder because: {}".format(product, e))
                self.convert_to_placeholder(product)
            created = False
        except Product.DoesNotExist as e:
            product = PlaceholderProduct(store=store, url=url, sku=sku)
            spider.logger.info("Saving placeholder {} because: {}".format(product, e))
            product.save()
            created = True
        except MultipleObjectsReturned:
            qs = Product.objects.filter(url=url, store=store)
            product = Product.merge_products(qs)
            product.in_stock = False
            created = False
        return (product, created)

    def convert_to_placeholder(self, product):
        """ Takes an existing product and converts it and its product tiles to placeholders """
        with disable_tile_serialization():
            placeholder = PlaceholderProduct.objects.get(id=product.id)
            placeholder.save()
        for t in placeholder.tiles.all():
            if t.template == "product":
                t.placeholder = True # will skip update_ir_cache
                t.save()


class TilesMixin(object):
    """
    Adds methods to handle tiles

    NOTE: Assumes global _category_cache <SimpleCache> exists
    """
    def __init__(self, *args, **kwargs):
        # Categories are cached in a module-level <SimpleCache>
        self.category_cache = category_cache
        super(TilesMixin, self).__init__(*args, **kwargs)
    
    @staticmethod
    def skip_tiles(item, spider):
        skip_tiles = [getattr(spider, 'skip_tiles', False), item.get('force_skip_tiles', False)]
        if True in skip_tiles:
            spider.logger.info(u"Skipping tile creation. \
                         spider.skip_tiles: {0}, item.force_skip_tiles: {1}".format(*skip_tiles))
            return True
        else:
            return False

    def add_to_feed(self, item, spider):
        obj = item['instance']
        feed_id = getattr(spider, 'feed_id', None)
        recreate_tiles = getattr(spider, 'recreate_tiles', False)
        categories = getattr(spider, 'categories', False)
        placeholder = getattr(obj, 'is_placeholder', False)

        try:
            feed = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            spider.logger.warning(u"Error adding to <Feed #{}> because feed does not exist".format(feed_id))
            raise CloseSpider(reason='Invalid feed id')

        if not item['created'] and recreate_tiles:
            spider.logger.info(u"Recreating tile for <{}>".format(obj))
            feed.remove(obj)

        if not categories:
            return feed.add(obj)
        elif len(categories) == 1:
            cname = categories[0]
            cat = self.category_cache.get_or_create(cname, store=item['store'])
            spider.logger.info(u"Adding <{}> to <{}>".format(obj, cat))
            tile, created = feed.add(obj, category=cat)
            tile.placeholder = placeholder
            tile.save()
            return (tile, created)
        else:
            tile, created = feed.add(obj)
            tile.placeholder = placeholder
            tile.save()
            for cname in categories:
                cat = self.category_cache.get_or_create(cname, store=item['store'])
                spider.logger.info(u"Adding <{}> to <{}>".format(obj, cat))
                cat.tiles.add(tile)
            return (tile, created)

