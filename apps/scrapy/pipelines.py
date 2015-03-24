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
from django.db.models import Model
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.exceptions import DropItem
from urlparse import urlparse

from apps.assets.models import Store, Product, Category, Feed, ProductImage, Image
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


# TODO: Many of these pipelines could likely be processors instead


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
        empty_fields = [k for (k, v) in item.items() if not v and k in required]
        if empty_fields:
            raise DropItem('Product fields cannot be blank: ({})'.format(
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


# Any changes to the item after this pipeline will not be persisted.
# It is suggested that this be the last pipeline
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


class TagWithProductsPipeline(object):
    """
    It saves a reference to content that passes through the pipeline
    and tags that content with any subsequent associated products
    """
    def __init__(self):
        self.images = {}

    def process_item(self, item, spider):
        if isinstance(item, ScraperImage) and item.get('tag_with_products') and item.get('content_id'):
            self.images[item.get('content_id')] = Image.objects.get(store__slug=spider.store_slug, url=item['url'])

        if isinstance(item, ScraperProduct) and item.get('content_id_to_tag'):
            content_id = item.get('content_id_to_tag')
            image = self.images.get(content_id)
            if image:
                product = Product.objects.get(store__slug=spider.store_slug, sku=item['sku'])
                if product:
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


class CategoryPipeline(object):
    def process_item(self, item, spider):
        if not isinstance(item, ScraperProduct):
            return item

        # if categories are given, add them
        categories = item.get('attributes', {}).get('categories', [])
        for name in categories:
            spider.log("Adding scraped category '{}'".format(name.strip()))
            self.add_to_category(item, name.strip())

        for category in getattr(spider, 'categories', []):
            spider.log("Adding spider-specified category '{}'".format(category.strip()))
            self.add_to_category(item, category.strip())

        return item

    def add_to_category(self, item, name):
        kwargs = {
            'store': item['store'],
            'name__iexact': name # django field lookup "iexact", meaning: ignore case
        }

        # temporary, we're clearing out duplicate categories.
        # Should dissociate all the products from all the different categories
        # and associate them with the "good" one (whichever has lowest id),
        # then delete the "bad" category.
        categories = Category.objects.filter(**kwargs)
        if len(categories) > 1:
            self.compress_duplicate_categories(categories)
        elif len(categories) == 1:
            category = categories[0]
        else:
            category = Category.objects.create(store=kwargs['store'], name=name.lower())

        category.name = category.name.lower()
        category.save()

        try:
            item_model = item_to_model(item)
        except TypeError, e:
            spider.log.WARNING('Error converting item to model, product not added to category {}:\n\t{}'.format(category.name, e))
            return

        product, _ = get_or_create(item_model)
        category.products.add(product)
        category.save()

    def compress_duplicate_categories(self, categories):
        spider.log("Compressing duplicate categories: {}".format(categories))
        category = categories[0]
        spider.log("\tKeeping: <Category {} {}>".format(category.id, category.name))
        for dup in categories[1:]:
            category.products.add(*dup.products.all())
            spider.log("\tTansferred {} products".format(dup.products.all()))
            spider.log("\tDeleting: <Category {} {}>".format(dup.id, dup.name))
            dup.delete()


class TileCreationPipeline(object):
    def process_item(self, item, spider):
        if item.get('force_skip_tiles', False):
            return item

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

        django_item, _ = get_or_create(item_model)

        feed.add(obj=django_item)


class ProductImagePipeline(object):
    def process_item(self, item, spider):
        remove_background = getattr(spider, 'remove_background', False)
        if isinstance(item, ScraperProduct):
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
                product = Product.objects.get(store__slug=spider.store_slug, sku=item['sku'])
                product.in_stock = False
                product.save()

            spider.log('Processed {} images'.format(successes))
            if failures:
                spider.log('{} images failed processing'.format(failures))
        return item

    def process_product_image(self, item, image_url, remove_background=False):
        store = item['store']
        product = item['sku']

        if not isinstance(product, Model):
            product = Product.objects.get(sku=product, store_id=store.id)

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
