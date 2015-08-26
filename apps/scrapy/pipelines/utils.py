from hashlib import md5

from django.core.exceptions import MultipleObjectsReturned
from scrapy.exceptions import CloseSpider

from apps.assets.models import Feed, Product
from apps.scrapy.items import ScraperProduct, ScraperContent, ScraperImage


class ItemManifold(object):
    """
    A Scrapy Pipeline that processes by scraper item type
    Pipeline is skipped if processor is not implemented for a type

    Supported items:

    ScraperProduct -> process_product
    ScraperContent -> process_content
    ScraperImage   -> process_image
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
        else:
            return item


class SimpleCache(object):
    """
    A simple module level cache
    """
    def __init__(self, model):
        self.model = model
        self.cache = defaultdict(dict)

    def get_or_create(self, name, store):
        try:
            # Check cache
            item = self.cache[store.slug][name]
        except KeyError:
            # Get or create category
            item, created = get_or_create(self.model(name=name, store=store))
            if created:
                item.save()
            # Add to cache
            self.cache[store.slug][name] = item
        return item

    def get(self, name, store):
        try:
            # Check cache
            item = self.cache[store.slug][name]
        except KeyError:
            # Get or create category
            item = None
        return item


class TilesMixin(object):
    """
    Adds methods to handle tiles

    NOTE: Assumes a global _category_cache <SimpleCache> exists
    """
    def __init__(self, *args, **kwargs):
        # Categories are cached in a module-level <SimpleCache>
        self.category_cache = _category_cache
        super(TilesMixin, self).__init__(*args, **kwargs)
    
    def skip_tiles(self, item, spider):
        skip_tiles = [getattr(spider, 'skip_tiles', False), item.get('force_skip_tiles', False)]
        spider.log(u"Skipping tile creation. spider.skip_tiles: {0}, item.force_skip_tiles: {1}".format(*skip_tiles))
        return bool(True in skip_tiles)

    def add_to_feed(self, item, spider, placeholder=False):
        feed_id = getattr(spider, 'feed_id', None)
        recreate_tiles = getattr(spider, 'recreate_tiles', False)
        categories = getattr(spider, 'categories', False)

        try:
            feed = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            spider.log(u"Error adding to <Feed {}> because feed does not exist".format(feed_id))
            raise CloseSpider(reason='Invalid feed id')

        obj = item['instance']

        if not item['created'] and recreate_tiles:
            spider.log(u"Recreating tile for <{}> {}".format(obj, item.get('name')))
            feed.remove(obj)

        if not categories:
            return feed.add(obj)
        elif len(categories) == 1:
            cname = categories[0]
            cat = self.category_cache.get_or_create(cname, store=item['store'])
            spider.log(u"Adding '{}' to <Category '{}'>".format(item.get('name'), cname))
            tile, created = feed.add(obj, category=cat)
            tile.reviewed = not placeholder
            tile.save()
            return (tile, created)
        else:
            tile, created = feed.add(obj)
            tile.reviewed = not placeholder
            tile.save()
            for cname in categories:
                cat = self.category_cache.get_or_create(cname, store=item['store'])
                spider.log(u"Adding '{}' to <Category '{}'>".format(item.get('name'), cname))
                cat.tiles.add(tile)
            return (tile, created)


class PlaceholderMixin(TileMixin):
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
                product = self.create_placeholder_product(store=store, url=url, sku=sku)
                created = True
            except MultipleObjectsReturned:
                ps = Product.objects.filter(url=url, store=store)
                not_placeholders = [ p for p in ps if not p.is_placeholder ]
                not_placeholders.sort(key=lambda p: p.created_at, reverse=True)
                # grab the most recent not placehoder, or the first placeholder
                product = not_placeholders[0] or ps[0]
                product.merge([ p for p in ps if p != product])
                created = False
            finally:
                item['instance'] = product
                item['created'] = created
                item['name'] = product.name

                # If we are creating tiles, add a placeholder to the feed
                if not self.skip_tiles(item, spider) and feed_id:
                    spider.log(u"Adding '{}' to <Feed {}>".format(product.name, feed_id))

                    recreate_tiles = getattr(spider, 'recreate_tiles', False)
                    categories = getattr(spider, 'categories', False)

                    self.add_to_feed(item, spider, placeholder=True)

    def create_placeholder_product(self, store, url, sku=None, name="placeholder"):
        if sku is None:
            # Make-up a temporary, unique SKU
            sku = "placeholder-{}".format(md5(url).hexdigest()) 
        return store.products.create(url=url, sku=sku, name=name,
                                     price=0, in_stock=False)

