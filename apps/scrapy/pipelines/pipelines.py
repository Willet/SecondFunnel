# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import cloudinary
import decimal
import logging
import traceback

from collections import defaultdict
from django.core.exceptions import ValidationError, MultipleObjectsReturned
from django.db import transaction
from django.db.models import Model, Q
from scrapy.exceptions import DropItem, CloseSpider
from urlparse import urlparse

from apps.assets.models import Category, Feed, Image, Page, Product, ProductImage, Store, Tag
from apps.assets.utils import disable_tile_serialization
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path
from apps.scrapy.utils.djangotools import item_to_model, get_or_create, update_model
from apps.scrapy.utils.misc import extract_decimal, extract_currency

from .mixins import ItemManifold, PlaceholderMixin, TilesMixin


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
            raise CloseSpider("Can't add items to non-existent store")

        item['store'] = store
        return item


class ValidationPipeline(ItemManifold, PlaceholderMixin, TilesMixin):
    """
    If item fails validation:
     - if product exists in database, set it to out of stock
     - if product doesn't exist in database, create a placeholder product
    Then, create placeholder tiles
    """
    def process_product(self, item, spider):
        # Drop items missing required fields
        required = set(['sku', 'name', 'price'])
        missing_fields = required - set([k for (k,v) in item.items()])
        empty_fields = [k for (k, v) in item.items() if k in required and not v]

        if missing_fields or empty_fields:
            # Attempt to find the product & mark it as out of stock
            item['instance'], item['created'] = self.update_or_save_placeholder(item)
            # If we are creating tiles, add (placeholder) to the feed
            if not self.skip_tiles(item, spider) and getattr(spider, 'feed_id', False):
                self.add_to_feed(item, spider)
            raise DropItem('Required fields missing ({}) or empty ({})'.format(
                    ', '.join(missing_fields),
                    ', '.join(empty_fields)
                ))
        return item


class DuplicatesPipeline(ItemManifold, TilesMixin):
    """
    Detects if there are duplicates based on sku and spider name.
    If so, drop this item and, if requested, create tiles with the 
    previous duplicate.
    """
    def __init__(self, *args, **kwargs):
        self.products_seen = defaultdict(set)
        self.content_seen = defaultdict(set)
        super(DuplicatesPipeline, self).__init__(*args, **kwargs)

    def process_product(self, item, spider):
        sku = item['sku']
        store = item['store']

        if sku in self.products_seen[spider.name]:
            if not self.skip_tiles(item, spider):
                product = Product.objects.get(store=store, sku=sku)
                item['instance'] = product
                self.add_to_feed(item, spider, placeholder=product.is_placeholder)
            raise DropItem("Duplicate item found here: {}".format(item))

        self.products_seen[spider.name].add(sku)

    def process_content(self, item, spider):
        # assuming source_url to be a unique attribute
        source_url = item['source_url']

        if source_url in self.content_seen[spider.name]:
            if not self.skip_tiles(item, spider):
                content = Content.objects.filter(store=store, source_url=source_url).select_subclasses()[0]
                item['instance'] = content
                self.add_to_feed(item, spider)
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

            spider.logger.info(u"\nprocessing image - {}".format(source_url))
            data = process_image(source_url, create_image_path(store.id), 
                                 remove_background=remove_background)
            item['url'] = data.get('url')
            item['file_type'] = data.get('format')
            item['dominant_color'] = data.get('dominant_color')
            item['source_url'] = source_url
            if not item.get('attributes', False):
                item['attributes'] = {}
            try:
                item['attributes']['sizes'] = data['sizes']
            except KeyError:
                item['attributes']['sizes'] = {}

            return item


class ItemPersistencePipeline(PlaceholderMixin, TilesMixin):
    """
    Save item as model

    Any changes to the item after this pipeline will not be automatically persisted!
    """
    def process_item(self, item, spider):
        try:
            item_model = item_to_model(item)
        except TypeError:
            raise DropItem("Item was not a known model, discarding: {}".format(item))

        model, was_it_created = get_or_create(item_model)
        item['created'] = was_it_created
        spider.logger.info(u"item: {}, created: {}".format(item, was_it_created))

        try:
             with disable_tile_serialization():
                # In case this item already exists, avoid serialization errors until later
                update_model(model, item)
        except ValidationError as e:
            # Attempt to find the product & mark it as out of stock
            item['instance'], item['created'] = self.update_or_save_placeholder(item)
            # If we are creating tiles, add (placeholder) to the feed
            if not self.skip_tiles(item, spider) and getattr(spider, 'feed_id', False):
                self.add_to_feed(item, spider)
            raise DropItem('DB item validation failed: ({})'.format(e))

        item['instance'] = model # save reference for further pipeline steps

        return item

# --- Item now has instance reference ---

class AssociateWithProductsPipeline(ItemManifold):
    """
    If a content has 'tag_with_products' field True and a 'content_id' field
    then tag with any subsequent products with 'content_id_to_tag' field matching
    'content_id'
    """
    def __init__(self, *args, **kwargs):
        self.images = {}
        super(AssociateWithProductsPipeline, self).__init__(*args, **kwargs)

    def process_image(self, item, spider):
        if item.get('tag_with_products') and item.get('content_id'):
            self.images[item.get('content_id')] = Image.objects.get(store=item['store'], url=item['url'])

    def process_product(self, item, spider):
        if item.get('content_id_to_tag'):
            content_id = item.get('content_id_to_tag')
            image = self.images.get(content_id)
            if image:
                product = item['instance']
                product_id = productsuct.id
                tagged_product_ids = image.tagged_products.values_list('id', flat=True)
                if not product_id in tagged_product_ids:
                    spider.logger.info(u'Tagging <Image {}> with <Product {}>'.format(image.id, product_id))
                    image.tagged_products.add(product)
                else:
                    spider.logger.info(u'<Image {}> already tagged with <Product {}>'.format(image.id, product_id))

    def close_spider(self, spider):
        # Save images in one transaction
        with transaction.atomic():
            for id in self.images:
                self.images[id].save()
        spider.logger.info(u'Saved {} tagged images'.format(len(self.images)))


class TagPipeline(ItemManifold):
    """
    If product or spider has tags, add them to <Product> items
    """
    def process_product(self, item, spider):
        # If tags were found by the crawler
        for name in item.get('attributes', {}).get('tags', []):
            spider.logger.info(u"Adding scraped tag '{}'".format(name.strip()))
            self.add_product_to_tag(item, name.strip())

        # If you want all products in a scrape to have a specific tag
        for name in getattr(spider, 'tags', []):
            spider.logger.info(u"Adding spider-specified tag '{}'".format(name.strip()))
            self.add_product_to_tag(item, name.strip())

    def add_product_to_tag(self, item, name):
        tag = Tag.objects.get(store=item['store'], name__iexact=name)
        tag.products.add(item['instance'])
        tag.save()


class ProductImagePipeline(ItemManifold, PlaceholderMixin):
    """
    If product has image_urls, turn them into <Product Image> and delete
    all other <Product Image>s that exist already
    """
    def process_product(self, item, spider):
        remove_background = getattr(spider, 'remove_background', False)
        skip_images = [getattr(spider, 'skip_images', False), item.get('force_skip_images', False)]
        store = item['store']
        sku = item['sku']
        product = item['instance']

        if True in skip_images:
            spider.logger.info(u"Skipping product images. item: <{0}>, spider.skip_images: {1}, \
                         item.force_skip_images: {2}".format(item.__class__.__name__, skip_images[0], skip_images[1]))
        else:
            old_images = list(product.product_images.all())
            images = []
            processed = 0

            for image_url in item.get('image_urls', []):
                url = urlparse(image_url, scheme='http').geturl()
                existing_image = next((old_images.pop(i) for i, pi in enumerate(old_images) \
                                      if pi.original_url == url), None)
                if not existing_image:
                    try:
                        images.append(self.process_product_image(item, url,
                                                                 remove_background=remove_background))
                        processed += 1
                    except cloudinary.api.Error as e:
                        spider.logger.info(u"<Product {}> image failed processing:\n{}".format(product, traceback.format_exc()))
                else:
                    images.append(existing_image)

            if not images:
                # Product has no images, convert to placeholder
                self.convert_to_placeholder(product)
                spider.logger.info(u"<Product {}> failed image processing!".format(product))
            else:
                # Product is good, delete any out of date images
                old_pks = [pi.pk for pi in old_images]
                product.product_images.filter(pk__in=old_pks).delete()
                product.default_image = spider.choose_default_image(product)
                product.save()
                spider.logger.info(u"<Product {}> has {} images, {} processed and {} deleted".format(
                                                    product, len(images), processed, len(old_pks)))
               

    def process_product_image(self, item, image_url, remove_background=False):
        store = item['store']
        product = item['instance']

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
            image.dominant_color = data['dominant_color']

            image.attributes['product_shot'] = image.is_product_shot
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


class TileCreationPipeline(TilesMixin):
    """ 
    If spider has feed_id, get or create tile(s) for product or content
    If spider also has category(s), add tile(s) to category(s)
    """
    def __init__(self, *args, **kwargs):
        super(TileCreationPipeline, self).__init__(*args, **kwargs)

    def process_item(self, item, spider):
        recreate_tiles = getattr(spider, 'recreate_tiles', False)
        categories = getattr(spider, 'categories', False)

        if self.skip_tiles(item, spider):
            return item
        else:
            feed_id = getattr(spider, 'feed_id', None)
            if feed_id:
                spider.logger.info(u"Adding '{}' to <Feed {}>".format(item.get('name'), feed_id))
                tile, _ = self.add_to_feed(item, spider)
            
            return item


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
    def __init__(self, *args, **kwargs):
        # set of product pk's for page, indexed by "store_slug-page_slug"
        self.not_updated_sets = {}
        super(PageUpdatePipeline, self).__init__(*args, **kwargs)

    def process_product(self, item, spider):
        if getattr(spider, 'page_update', False):
            # This product has been updated
            store = item['store']
            sku = item['sku']
            page_slug = getattr(spider, 'page_slug', False)

            if store.slug and page_slug:
                key = '{}-{}'.format(store.slug, page_slug)
                pk = item['instance'].pk
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
                spider.logger.info(u'Marked {} products as sold out'.format(len(pk_set)))

