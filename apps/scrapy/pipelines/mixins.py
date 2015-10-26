from django.core.exceptions import MultipleObjectsReturned
from scrapy.exceptions import CloseSpider

from apps.assets.models import Category, Feed, Product
from apps.assets.utils import disable_tile_serialization
from apps.intentrank.serializers import SerializerError
from apps.scrapy.items import ScraperProduct, ScraperContent, ScraperImage
from apps.scrapy.models import PlaceholderProduct

from .utils import SimpleModelCache


category_cache = SimpleModelCache(Category)


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

