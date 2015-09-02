from django.core.exceptions import MultipleObjectsReturned
from scrapy.exceptions import CloseSpider

from apps.assets.models import Category, Feed, Product
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
    
    def skip_tiles(self, item, spider):
        skip_tiles = [getattr(spider, 'skip_tiles', False), item.get('force_skip_tiles', False)]
        if True in skip_tiles:
            spider.log(u"Skipping tile creation. \
                         spider.skip_tiles: {0}, item.force_skip_tiles: {1}".format(*skip_tiles))
            return True
        else:
            return False

    def add_to_feed(self, item, spider, placeholder=False):
        feed_id = getattr(spider, 'feed_id', None)
        recreate_tiles = getattr(spider, 'recreate_tiles', False)
        categories = getattr(spider, 'categories', False)

        try:
            feed = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            spider.log(u"Error adding to <Feed #{}> because feed does not exist".format(feed_id))
            raise CloseSpider(reason='Invalid feed id')

        obj = item['instance']

        if not item['created'] and recreate_tiles:
            spider.log(u"Recreating tile for <{}>".format(obj))
            feed.remove(obj)

        if not categories:
            return feed.add(obj)
        elif len(categories) == 1:
            cname = categories[0]
            cat = self.category_cache.get_or_create(cname, store=item['store'])
            spider.log(u"Adding <{}> to <{}>".format(obj, cat))
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
                spider.log(u"Adding <{}> to <{}>".format(obj, cat))
                cat.tiles.add(tile)
            return (tile, created)


class PlaceholderMixin(TilesMixin):
    """
    Adds methods to create placeholder products and tiles

    NOTE: Assumes a global _category_cache <SimpleCache> exists
    """
    def __init__(self, *args, **kwargs):
        super(PlaceholderMixin, self).__init__(*args, **kwargs)

    def update_or_save_placeholder(self, item, spider):
        url = item['url']
        store = item['store']
        sku = item.get('sku', None)

        feed_id = getattr(spider, 'feed_id', None)

        try:
            product = Product.objects.get(url=url, store=store)
            product.in_stock = False
            product.save()
            created = False
        except Product.DoesNotExist:
            product = PlaceholderProduct(store=store, url=url, sku=sku)
            product.save()
            created = True
        except MultipleObjectsReturned:
            qs = Product.objects.filter(url=url, store=store)
            product = Product.merge_products(qs)
            created = False
        finally:
            # If we are creating tiles, add a placeholder to the feed
            if not self.skip_tiles(item, spider) and feed_id:
                item['instance'] = product
                item['created'] = created
                spider.log(u"Adding '{}' to <Feed #{}>".format(product, feed_id))

                recreate_tiles = getattr(spider, 'recreate_tiles', False)
                categories = getattr(spider, 'categories', False)

                self.add_to_feed(item, spider, placeholder=product.is_placeholder)

