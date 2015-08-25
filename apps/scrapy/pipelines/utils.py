from scrapy.exceptions import CloseSpider

from apps.assets.models import Feed
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


class TileOpsMixin(object):
    """
    Adds a method to add a tile to feed.
    Assumes a local self._category_cache <SimpleCache> exists
    """
    def __init__(self, *args, **kwargs):
        # Categories are cached in a module-level <SimpleCache>
        self.category_cache = _category_cache
        super(AddToFeedMixin, self).__init__(*args, **kwargs)

    def save_stub(self, item, spider):
            url = item.get('url', None)
            sku = item.get('sku', None)
            store = item['store']

            query = Q(url=url, store=store) if url else \
                    Q(sku=sku, store=store) if sku else None

            recreate_tiles = getattr(spider, 'recreate_tiles', False)
            categories = getattr(spider, 'categories', False)
            feed_id = getattr(spider, 'feed_id', None)

            try:
                product = Product.objects.get(query)
                product.in_stock = False
                product.save()
                created = False
                exception =  DropItem('OutOfStock')
            except (Product.DoesNotExist, TypeError):
                # TypeError happens if query is None
                # This item doesn't exist yet
                product = self.create_stub_product(store=store, url=url, sku=sku)
                created = True
                exception = DropItem('Required fields missing ({}) or empty ({})'.format(
                    ', '.join(missing_fields),
                    ', '.join(empty_fields)
                ))
            finally:
                item['instance'] = product
                item['created'] = created
                item['name'] = product.name

                # If we are creating tiles, add a placeholder to the feed
                if not self.skip_tiles(spider) and feed_id:
                    # Create tile for each feed
                    spider.log(u"Adding '{}' to <Feed {}>".format(product.name, feed_id))
                    self.add_to_feed(item, feed_id, recreate_tiles, categories,
                                     placeholder=True, logger=spider.log)
                # Drop item
                return exception

    def create_stub_product(self, ...):
        

    def skip_tiles(self, spider):
        skip_tiles = [getattr(spider, 'skip_tiles', False), item.get('force_skip_tiles', False)]
        spider.log(u"Skipping tile creation. spider.skip_tiles: {0}, item.force_skip_tiles: {1}".format(*skip_tiles))
        return bool(True in skip_tiles)

    def add_to_feed(self, item, feed_id, recreate_tiles=False,
                    categories=[], placeholder=False, logger=lambda x: None):
        try:
            feed = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            logger(u"Error adding to <Feed {}> because feed does not exist".format(feed_id))
            raise CloseSpider(reason='Invalid feed id')

        obj = item['instance']

        if not item['created'] and recreate_tiles:
            logger(u"Recreating tile for <{}> {}".format(obj, item.get('name')))
            feed.remove(obj)

        if not categories:
            return feed.add(obj)
        elif len(categories) == 1:
            cname = categories[0]
            cat = self.category_cache.get_or_create(cname, store=item['store'])
            logger(u"Adding '{}' to <Category '{}'>".format(item.get('name'), cname))
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
                logger(u"Adding '{}' to <Category '{}'>".format(item.get('name'), cname))
                cat.tiles.add(tile)
            return (tile, created)

