# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import cloudinary
import traceback
import decimal

from collections import defaultdict
from django.core.exceptions import ValidationError, MultipleObjectsReturned
from django.db import transaction
from django.db.models import Model, Q
from scrapy import log
from scrapy.exceptions import DropItem
from urlparse import urlparse

from apps.assets.models import Category, Feed, Image, Page, Product, ProductImage, Store, Tag
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path
from apps.scrapy.items import ScraperProduct, ScraperContent, ScraperImage
from apps.scrapy.utils.django import item_to_model, get_or_create, update_model
from apps.scrapy.utils.misc import extract_decimal, extract_currency


class ItemManifold(object):
    """
    A Scrapy Pipeline that processes by scraper item type
    Pipeline is skipped if processor is not implemented for a type

    Supported items:

    ScraperProduct -> process_product
    ScraperContent -> process_content
    ScraperImage   -> process_image
    """
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


class ForeignKeyPipeline(ItemManifold):
    """ Currently turns item['store'] into a <Store> instance """
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


class ValidationPipeline(ItemManifold):
    """
    If item fails validation, drop item & do something intelligent if its already in the database
    """
    def process_product(self, item, spider):
        # Drop items missing required fields
        required = set(['sku', 'name'])
        missing_fields = required - set([k for (k,v) in item.items()])
        empty_fields = [k for (k, v) in item.items() if k in required and not v]
        if missing_fields or empty_fields:
            # If we are missing required fields, attempt to find the product & mark it as out of stock
            sku = item.get('sku', None)
            url = item.get('url', None)

            store_slug = getattr(spider, 'store_slug', '')
            store = Store.objects.get(slug=store_slug)

            query = Q(sku=sku, store=store)|Q(url=url, store=store) if sku and url else \
                    Q(sku=sku, store=store) if sku else \
                    Q(url=url, store=store) if url else None

            try:
                product = Product.objects.get(query)
                product.in_stock = False
                product.save()

                raise DropItem('OutOfStock')
            except (Product.DoesNotExist, TypeError):
                # TypeError happens if the query includes Q(None)
                # This item doesn't exist yet
                raise DropItem('Required fields missing ({}) or empty ({})'.format(
                    ', '.join(missing_fields),
                    ', '.join(empty_fields)
                ))

        return item


class DuplicatesPipeline(ItemManifold):
    """
    Detects if there are duplicates based on sku and spider name.

    TODO: merge duplicates?
    """
    def __init__(self):
        self.products_seen = defaultdict(set)
        self.content_seen = defaultdict(set)

    def process_product(self, item, spider):
        sku = item['sku']

        if sku in self.products_seen[spider.name]:
            raise DropItem("Duplicate item found here: {}".format(item))

        self.products_seen[spider.name].add(sku)

    def process_content(self, item, spider):
        # assuming source_url to be a unique attribute
        source_url = item['source_url']

        if source_url in self.content_seen[spider.name]:
            raise DropItem("Duplicate item found: {}".format(item))

        self.content_seen[spider.name].add(source_url)


class PricePipeline(ItemManifold):
    """
    Converts price & sale_price to decimal.Decimal & stores currency
    Note: currency is *any* characters around price that aren't numbers, decimal, or whitespace
    """
    def process_product(self, item, spider):
        if not isinstance(item['price'], decimal.Decimal):
            price = item['price']

            item['price'] = extract_decimal(price)
            item['currency'] = extract_currency(price)

        sale_price = item.get('sale_price', None)
        if sale_price and not isinstance(sale_price, decimal.Decimal):
            item['sale_price'] = extract_decimal(sale_price)
        return item


class ContentImagePipeline(ItemManifold):
    """
    Load image up to Cloudinary and store image details
    """
    def process_image(self, item, spider):
        source_url = item.get('source_url', False)
        if source_url:
            if item.get('url', False) and item.get('file_type', False):
                # Already sufficiently proccessed
                return item

            spider.log("\nprocessing image - {}".format(source_url))
            data = process_image(source_url, create_image_path(store.id), remove_background=remove_background)
            item['url'] = data.get('url')
            item['file_type'] = data.get('format')
            item['dominant_color'] = data.get('dominant_colour')
            item['source_url'] = source_url
            if not item.get('attributes', False):
                item['attributes'] = {}
            try:
                item['attributes']['sizes'] = data['sizes']
            except KeyError:
                item['attributes']['sizes'] = {}

            return item


class ItemPersistencePipeline(object):
    """
    Save item as model

    Any changes to the item after this pipeline will not be automaticlaly persisted!
    """
    def process_item(self, item, spider):
        try:
            item_model = item_to_model(item)
        except TypeError:
            return item

        model, was_it_created = get_or_create(item_model)
        item['created'] = was_it_created
        try:
            update_model(model, item)
        except ValidationError as e:
            raise DropItem('DB item validation failed: ({})'.format(e))

        if isinstance(item, ScraperProduct):
            item['product'] = model

        elif isinstance(item, ScraperContent):
            item['content'] = model

        return item


class AssociateWithProductsPipeline(ItemManifold):
    """
    If a content has 'tag_with_products' field True and a 'content_id' field
    then tag with any subsequent products with 'content_id_to_tag' field matching
    'content_id'
    """
    def __init__(self):
        self.images = {}

    def process_image(self, item, spider):
        if item.get('tag_with_products') and item.get('content_id'):
            self.images[item.get('content_id')] = Image.objects.get(store=item['store'], url=item['url'])

    def process_product(self, item, spider):
        if item.get('content_id_to_tag'):
            content_id = item.get('content_id_to_tag')
            image = self.images.get(content_id)
            if image:
                product = item['product']
                product_id = product.id
                tagged_product_ids = image.tagged_products.values_list('id', flat=True)
                if not product_id in tagged_product_ids:
                    spider.log('Tagging <Image {}> with <Product {}>'.format(image.id, product_id))
                    image.tagged_products.add(product)
                else:
                    spider.log('<Image {}> already tagged with <Product {}>'.format(image.id, product_id))

    def close_spider(self, spider):
        # Save images in one transaction
        with transaction.atomic():
            for id in self.images:
                self.images[id].save()
        spider.log('Saved {} tagged images'.format(len(self.images)))


class TagPipeline(ItemManifold):
    """
    If product or spider has tags, add them to <Product> items
    """
    def process_product(self, item, spider):
        # If tags were found by the crawler
        for name in item.get('attributes', {}).get('tags', []):
            spider.log("Adding scraped tag '{}'".format(name.strip()))
            self.add_product_to_tag(item, name.strip())

        # If you want all products in a scrape to have a specific tag
        for name in getattr(spider, 'tags', []):
            spider.log("Adding spider-specified tag '{}'".format(name.strip()))
            self.add_product_to_tag(item, name.strip())

    def add_product_to_tag(self, item, name):
        tag = Tag.objects.get(store=item['store'], name__iexact=name)
        tag.products.add(item['product'])
        tag.save()


class ProductImagePipeline(ItemManifold):
    """
    If product has image_urls, turn them into <Product Image> if they don't exist already
    """
    def process_product(self, item, spider):
        remove_background = getattr(spider, 'remove_background', False)
        skip_images = getattr(spider, 'skip_images', False)
        store = item['store']
        sku = item['sku']

        if skip_images:
            spider.log(u"Skipping product images. item: <{}>, spider.skip_images: {}".format(item.__class__.__name__, skip_images))
        else:
            successes = 0
            failures = 0
            for image_url in item.get('image_urls', []):
                url = urlparse(image_url, scheme='http')
                try:
                    self.process_product_image(item, url.geturl(), remove_background=remove_background)
                    successes += 1
                except cloudinary.api.Error as e:
                    traceback.print_exc()
                    failures += 1
            if not successes:
                # if product has no images, we don't want
                # to show it on the page.
                # Implementation is not very idiomatic unfortunately
                product = item['product']
                product.in_stock = False
                product.save()

            spider.log(u"Processed {} images".format(successes))
            if failures:
                spider.log(u"{} images failed processing".format(failures))

    def process_product_image(self, item, image_url, remove_background=False):
        store = item['store']
        product = item['product']

        # Doesn't this mean that if we ever end up seeing the same URL twice,
        # then we'll create new product images if the product differs?
        try:
            image = ProductImage.objects.get(original_url=image_url, product=product)
        except ProductImage.DoesNotExist:
            image = ProductImage(original_url=image_url, product=product)

        # this image needs to be uploaded
        if not (image.url and image.file_type):
            print '\nprocessing image - ' + image_url
            data = process_image(image_url, create_image_path(store.id),
                                 remove_background=remove_background)
            image.url = data.get('url')
            image.file_type = data.get('format')
            image.dominant_color = data.get('dominant_colour')

            image.attributes['sizes'] = data['sizes']

            # save the image
            image.save()

            if product and not product.default_image:
                product.default_image = image
                product.save()
        else:
            print '\nimage has already been processed'

        print image.to_json()

        return image


class TileCreationPipeline(object):
    """ 
    If spider has feed_id, get or create tile(s) for product or content
    If spider also has category(s), add tile(s) to category(s)
    """
    def __init__(self):
        # Categories will be indexed by id
        self.category_cache = defaultdict(dict)

    def process_item(self, item, spider):
        recreate_tiles = getattr(spider, 'recreate_tiles', False)
        skip_tiles = [getattr(spider, 'skip_tiles', False), item.get('force_skip_tiles', False)]
        categories = getattr(spider, 'categories', False)

        if True in skip_tiles:
            spider.log(u"Skipping tile creation. spider.skip_tiles: {0}, item.force_skip_tiles: {1}".format(*skip_tiles))
            return item
        else:
            feed_id = getattr(spider, 'feed_id', None)

            if feed_id:
                # Create tile for each feed
                spider.log(u"Adding '{}' to <Feed {}>".format(item.get('name'), feed_id))
                tile, _ = self.add_to_feed(item, feed_id, recreate_tiles)
                if categories:
                    # Add each tile to the categories
                    for cname in categories:
                        spider.log(u"Adding '{}' to <Category '{}'>".format(item.get('name'), cname))
                        self.add_to_category(tile, cname, item['store'])

            return item

    def add_to_feed(self, item, feed_id, recreate_tiles=False):
        try:
            feed = Feed.objects.get(id=feed_id)
        except Feed.DoesNotExist:
            spider.log(u"Error adding to <Feed {}> because feed does not exist".format(feed_id))
            return

        if isinstance(ScraperProduct):
            obj = item['product']
        elif isinstance(ScraperContent):
            obj = item['content']

        if not item['created'] and recreate_tiles:
            spider.log(u"Recreating tile for <{}> {}".format(obj, item.get('name')))
            feed.remove(obj)

        return feed.add(obj)

    def add_to_category(self, tile, category_name, store):
        try:
            # Check cache
            cat = self.category_cache[store.slug][category_name]
        except KeyError:
            # Get or create category
            cat, created = get_or_create(Category(name=category_name, store=store))
            if created:
                cat.save()
            # Add to cache
            self.category_cache[store.slug][category_name] = cat
        cat.tiles.add(tile)


class SimilarProductsPipeline(ItemManifold):
    pass


class PageUpdatePipeline(ItemManifold):
    """ During a page update, catch any product that is not updated & set it to out of stock
    
    To enable:
        a) spider must have 'page_update' field set to True
        b) spider must have a valid 'page_slug' field

    TODO: items that have remained out of stock for a sufficiently long time (1 or 2 weeks?)
          should be deleted
    """
    def __init__(self):
        # set of product pk's for page, indexed by "store_slug-page_slug"
        self.not_updated_sets = {}

    def process_product(self, item, spider):
        if getattr(spider, 'page_update', False):
            # This product has been updated
            store = item['store']
            sku = item['sku']
            page_slug = getattr(spider, 'page_slug', False)

            if isinstance(item, ScraperProduct) and store.slug and page_slug:
                key = '{}-{}'.format(store.slug, page_slug)
                pk = item['product'].pk
                pk_set = self.not_updated_sets[key]
                try:
                    pk_set.remove(pk)
                except KeyError:
                    # If this is a new product from the datafeed, it will not be in the set
                    pass

    def spider_opened(self, spider):
        """ Create list of products for this page """
        if getattr(spider, 'page_update', False):
            store_slug = getattr(spider, 'store_slug', False)
            page_slug = getattr(spider, 'page_slug', False)
            key = '{}-{}'.format(store_slug, page_slug)

            try:
                page = Page.objects.get(url_slug=page_slug, store__slug=store_slug)
            except Page.DoesNotExist:
                pass
            else:
                # ensure key is unique
                if key in self.not_updated_cache:
                    # Two spiders should not be updating a datafeed at the same time
                    raise ValueError("Page '{}' feed update already initialized, can't initialize twice".format(page_slug))
                # Store pk set of products
                self.not_updated_sets[key] = page.feed.get_all_products(pk_set=True)

    def close_spider(self, spider):
        """ Mark all products that were not updated as out of stock """
        if getattr(spider, 'page_update', False):
            store_slug = getattr(spider, 'store_slug', False)
            page_slug = getattr(spider, 'page_slug', False)
            key = '{}-{}'.format(store_slug, page_slug)

            try:
                pk_set = self.not_updated_sets[key]
            except KeyError:
                pass
            else:
                # Mark all items in not_updated_cache as out of stock
                Product.objects.filter(pk__in=pk_set).update(in_stock=False)
                spider.log('Marked {} products as sold out'.format(len(pk_set)))

