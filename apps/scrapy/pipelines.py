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
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from urlparse import urlparse

from apps.assets.models import Category, Feed, Image, Product, ProductImage, Store, Tag
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path
from apps.scrapy.items import ScraperProduct, ScraperContent, ScraperImage
from apps.scrapy.utils.django import item_to_model, get_or_create, update_model
from apps.scrapy.utils.misc import CloudinaryStore, extract_decimal, extract_currency


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


class ValidationPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
            return self.process_product(item, spider)

        elif isinstance(item, ScraperContent):
            return self.process_content(item, spider)

        return item

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

    def process_content(self, item, spider):
        return item


class PricePipeline(object):
    """
    Converts price & sale_price to decimal.Decimal & stores currency
    Note: currency is *any* characters around price that aren't numbers, decimal, or whitespace
    """
    def process_item(self, item, spider):
        if isinstance(item, ScraperProduct):
            if not isinstance(item['price'], decimal.Decimal):
                price = item['price']

                item['price'] = extract_decimal(price)
                item['currency'] = extract_currency(price)

            sale_price = item.get('sale_price', None)
            if sale_price and not isinstance(sale_price, decimal.Decimal):
                item['sale_price'] = extract_decimal(sale_price)

        return item


class DuplicatesPipeline(object):
    """
    Detects if there are duplicates based on sku and spider name.

    Alternatively, we could do some sort of merge if there are duplicates...
    """
    def __init__(self):
        self.ids_seen = defaultdict(set)
        self.content_seen = defaultdict(set)

    def process_item(self, item, spider):
        spider_name = spider.name
        if isinstance(item, ScraperProduct):
            sku = item['sku']

            if sku in self.ids_seen[spider_name]:
                raise DropItem("Duplicate item found here: {}".format(item))

            self.ids_seen[spider_name].add(sku)
        if isinstance(item, ScraperContent):
            # assuming source_url to be a unique attribute
            source_url = item['source_url']

            if source_url in self.content_seen[spider_name]:
                raise DropItem("Duplicate item found: {}".format(item))

            self.content_seen[spider_name].add(source_url)
        return item


# At the moment, ForeignKeys are a bitch, so, handle those separately.
class ForeignKeyPipeline(object):
    """ Currently turns item['store'] into a <Store> instance """
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


class ContentImagePipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, ScraperImage):
            if item.get('source_url', False):
                item = self.process_image(item['source_url'], item, item['store'])
        return item

    def process_image(self, source_url, image, store, remove_background=False):
        if image.get('url', False) and image.get('file_type', False) and image.get('source_url', False):
            return image

        print '\nprocessing image - ' + source_url
        data = process_image(source_url, create_image_path(store.id), remove_background=remove_background)
        image['url'] = data.get('url')
        image['file_type'] = data.get('format')
        image['dominant_color'] = data.get('dominant_colour')
        image['source_url'] = source_url
        if not image.get('attributes', False):
            image['attributes'] = {}
        try:
            image['attributes']['sizes'] = data['sizes']
        except KeyError:
            image['attributes']['sizes'] = {}

        return image


# Any changes to the item after this pipeline will not be persisted!
class ItemPersistencePipeline(object):
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

        return item


class AssociateWithProductsPipeline(object):
    """
    It saves a reference to content that passes through the pipeline
    and tags that content with any subsequent associated products
    """
    def __init__(self):
        self.images = {}

    def process_item(self, item, spider):
        store = item['store']
        url = item['url']

        if isinstance(item, ScraperImage) and item.get('tag_with_products') and item.get('content_id'):
            self.images[item.get('content_id')] = Image.objects.get(store=store, url=url)

        if isinstance(item, ScraperProduct) and item.get('content_id_to_tag'):
            content_id = item.get('content_id_to_tag')
            image = self.images.get(content_id)
            if image:
                product = Product.objects.get(stores=store, sku=item['sku'])
                product_id = product.id
                tagged_product_ids = image.tagged_products.values_list('id', flat=True)
                if not product_id in tagged_product_ids:
                    spider.log('Tagging <Image {}> with <Product {}>'.format(image.id, product_id))
                    image.tagged_products.add(product)
                else:
                    spider.log('<Image {}> already tagged with <Product {}>'.format(image.id, product_id))

        return item

    def close_spider(self, spider):
        # Save images in one transaction
        with transaction.atomic():
            for id in self.images:
                self.images[id].save()
        spider.log('Saved {} tagged images'.format(len(self.images)))


class TagPipeline(object):
    def process_item(self, item, spider):
        if not isinstance(item, ScraperProduct):
            return item

        # If tags were found by the crawler
        tags = item.get('attributes', {}).get('tags', [])
        for name in tags:
            spider.log("Adding scraped tag '{}'".format(name.strip()))
            self.add_to_tag(item, name.strip())

        # If you want all products in a scrape to have a specific tag
        for tag in getattr(spider, 'tags', []):
            spider.log("Adding spider-specified tag '{}'".format(tag.strip()))
            self.add_to_tag(item, tag.strip())

        return item

    def add_to_tag(self, item, name):
        kwargs = {
            'store': item['store'],
            'name__iexact': name # django field lookup "iexact", meaning: ignore case
        }

        # temporary, we're clearing out duplicate tags.
        # Should dissociate all the products from all the different tags
        # and associate them with the "good" one (whichever has lowest id),
        # then delete the "bad" tag
        tags = Tag.objects.filter(**kwargs)
        if len(tags) > 1:
            self.compress_duplicate_tags(tags)
        elif len(tags) == 1:
            tag = tags[0]
        else:
            tag = Tag.objects.create(**kwargs)

        tag.name = tag.name.lower()
        tag.save()

        try:
            item_model = item_to_model(item)
        except TypeError, e:
            spider.log.WARNING('Error converting item to model, product not added to tag {}:\n\t{}'.format(tag.name, e))
            return

        product, _ = get_or_create(item_model)
        tag.products.add(product)
        tag.save()

    def compress_duplicate_tags(self, tags):
        spider.log(u"Compressing duplicate tags: {}".format(tags))
        tag = tags[0]
        spider.log(u"\tKeeping: <Tag {} {}>".format(tag.id, tag.name))
        for dup in tags[1:]:
            tag.products.add(*dup.products.all())
            spider.log(u"\tTansferred {} products".format(dup.products.all()))
            spider.log(u"\tDeleting: <Tag {} {}>".format(dup.id, dup.name))
            dup.delete()


class TileCreationPipeline(object):
    """ 
    If spider has feed(s), create tile(s) for product or content
    If spider also has category(s), add tile(s) to category(s)
    """
    def __init__(self):
        # Categories will be indexed by id
        self.category_cache = {}

    def process_item(self, item, spider):
        recreate_tiles = getattr(spider, 'recreate_tiles', False)
        skip_tiles = [getattr(spider, 'skip_tiles', False), item.get('force_skip_tiles', False)]
        categories = getattr(spider, 'categories', False)

        if True in skip_tiles:
            spider.log(u"Skipping tile creation. spider.skip_tiles: {0}, item.force_skip_tiles: {1}".format(*skip_tiles))
            return item
        else:
            feed_ids = getattr(spider, 'feed_ids', [])

            # Supports multiple feeds and multiple categories
            if feed_ids:
                for fid in feed_ids:
                    # Create tile for each feed
                    spider.log(u"Adding '{}' to <Feed {}>".format(item.get('name'), fid))
                    tile, _ = self.add_to_feed(item, fid, recreate_tiles)
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
            return

        try:
            item_model = item_to_model(item)
        except TypeError:
            return

        item_obj, created = get_or_create(item_model)

        if not created and recreate_tiles:
            spider.log(u"Recreating tile for <{}> {}".format(item_obj, item.get('name')))
            feed.remove(item_obj)

        return feed.add(item_obj)

    def add_to_category(self, tile, category_name, store):
        # Add store_slug to category_cache
        if not self.category_cache.get(store.slug, False):
            self.category_cache[store.slug] = {}

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


class ProductImagePipeline(object):
    def process_item(self, item, spider):
        remove_background = getattr(spider, 'remove_background', False)
        skip_images = getattr(spider, 'skip_images', False)
        store = item['store']

        if isinstance(item, ScraperProduct) and not skip_images:
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
                product = Product.objects.get(store=store, sku=item['sku'])
                product.in_stock = False
                product.save()

            spider.log(u"Processed {} images".format(successes))
            if failures:
                spider.log(u"{} images failed processing".format(failures))
        else:
            spider.log(u"Skipping product images. item: <{}>, spider.skip_images: {}".format(item.__class__.__name__, skip_images))
        return item

    def process_product_image(self, item, image_url, remove_background=False):
        store = item['store']
        sku = item['sku']

        if not isinstance(product, Model):
            product = Product.objects.get(sku=sku, store=store)

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
