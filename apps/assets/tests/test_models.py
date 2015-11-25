from django.core.management import call_command
from django.db.models.base import ModelBase
from django.db import models, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
import mock
import datetime
import time
import factory
import mock
from decimal import *
from django.test import TestCase

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
from apps.imageservice.utils import delete_cloudinary_resource, delete_s3_resource
from apps.assets.utils import disable_tile_serialization

"""
We are avoiding fixtures because they are so slow:
http://www.mattjmorrison.com/2011/09/mocking-django.html
"""

# class ProductFactory(factory.Factory):
#     class Meta:
#         model = Product

# class ProductImageFactory(factory.Factory):
#     class Meta:
#         model = ProductImage

# class StoreFactory(factory.Factory):
#     class Meta:
#         model = Store
#     name = "Test Store"
#     slug = "test_store"

# class FeedFactory(factory.Factory):
#     class Meta:
#         model = Feed
#     id=1

# class BaseModelTest(TestCase):
#     def setUp(self):
#         # create a dummy model to inherit abstract class BaseModel
#         self.model = ModelBase(BaseModel)

class StoreTest(TestCase):
    # Store has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        self.store = Store.objects.get(pk=1)
        self.assertEqual(self.store.slug, "store_slug")
        self.assertEqual(self.store.name, "MyStore")
        self.assertIsNot(self.store.cg_created_at, None)
        self.assertIsNot(self.store.cg_updated_at, None)
        self.assertTrue(self.store.id > 0)

class ThemeTest(TestCase):
    # Theme has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        t = Theme.objects.get(pk=2)
        self.assertIsNot(t.cg_created_at, None)
        self.assertIsNot(t.cg_updated_at, None)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, "Default")
        self.assertTrue(t.pk > 0)
        self.assertTrue(len(t.template) > 0)

    def load_theme_test(self):
        t = Theme.objects.get(pk=2)
        self.assertEqual(t.load_theme(), u'mystore/landingpage/default/index.html')

class ProductTest(TestCase):
    # Product has a method - clean
    fixtures = ['assets_models.json']

    def properties_test(self):
        pprice = 19.99
        store_id = 1
        p = Product.objects.get(pk=3)
        self.assertIsNot(p.cg_created_at, None)
        self.assertIsNot(p.cg_updated_at, None)
        self.assertEqual(p.store_id, store_id)
        self.assertEqual(float(p.price), pprice)
        self.assertTrue(p.id > 0)

    def blank_clean_test(self):
        p = Product.objects.get(pk=3)
        p.clean()
        self.assertEqual(p.attributes, {})

    def one_image_clean_test(self):
        p = Product.objects.get(pk=3)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        Product.clean(p)
        self.assertEqual(p.default_image, i)

    def two_image_clean_test(self):
        p = Product.objects.get(pk=3)
        i1 = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11)
        p.product_images.add(i1)
        p.product_images.add(i2)
        Product.clean(p)
        self.assertEqual(p.default_image, i1)

    def two_image_clean_order_test(self):
        p = Product.objects.get(pk=3)
        i1 = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11)
        p.product_images.add(i2)
        p.product_images.add(i1)
        Product.clean(p)
        self.assertEqual(p.default_image, i2)

    def blank_clean_fields_test(self):
        p = Product.objects.get(pk=3)
        p.price = None
        p.clean_fields()
        self.assertFalse(p.price)

    def type_clean_fields_test(self):
        price = 19.99
        p = Product.objects.get(pk=3)
        p.clean_fields()
        self.assertNotEqual(p.price, price)

    def error_clean_fields_test(self):
        with self.assertRaises(ValidationError):
            p = Product.objects.get(pk=3)
            p.price = "Error"
            p.clean_fields()

    def exclude_clean_fields_test(self):
        p = Product.objects.get(pk=3)
        p.price = "Error"
        p.clean_fields(["price"])

    #BROKEN
    
#     Traceback (most recent call last):
#   File "/opt/secondfunnel/app/apps/assets/tests/test_models.py", line 148, in merge_test
#     p.merge(p2)
#   File "/opt/secondfunnel/app/apps/assets/models.py", line 497, in merge
#     other_products = list(other_products)
#   File "/opt/secondfunnel/app/apps/assets/models.py", line 78, in __getitem__
#     return getattr(self, key, None)
# TypeError: getattr(): attribute name must be string

    # def merge_test(self):
    #     p = Product.objects.get(pk=3)
    #     p2 = Product.objects.get(pk=15)
    #     i = ProductImage.objects.get(pk=4)
    #     p2.product_images.add(i)
    #     p.merge(p2)
    #     # assure product has been deleted
    #     # with self.assertRaises(ObjectDoesNotExist):
    #     Product.objects.get(pk=15)



class ProductImageTest(TestCase):
    # ProductImage has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        url = "/image.jpg"
        original_url = "test.com/image.jpg"
        product_image = ProductImage.objects.get(pk=4)
        self.assertIsNot(product_image.cg_created_at, None)
        self.assertIsNot(product_image.cg_updated_at, None)
        self.assertTrue(product_image.id > 0)
        self.assertIsNone(product_image.ir_cache)
        self.assertTrue(product_image.pk > 0)
        self.assertEqual(product_image.url, url)
        self.assertEqual(product_image.original_url, original_url)

    def save_test(self):
        t = ProductImage.objects.get(pk=4)
        self.assertIsNone(t.width)
        self.assertIsNone(t.height)
        with self.assertRaises(KeyError):
            self.assertIsNone(t.attributes['sizes'])
        t.save()
        self.assertEqual(t.width, 0)
        self.assertEqual(t.height, 0)

    def save_dimensions_test(self):
        t = ProductImage.objects.get(pk=4)
        t.attributes['sizes'] = {
            "master": {
                "width": 640,
                "height": 480
            }
        }
        self.assertIsNone(t.width)
        self.assertIsNone(t.height)
        self.assertIsNotNone(t.attributes['sizes'])
        t.save()
        self.assertEqual(t.width, 640)
        self.assertEqual(t.height, 480)
        self.assertEqual(t.orientation, "landscape")

    @mock.patch('apps.imageservice.utils.delete_cloudinary_resource', mock.Mock())
    def delete_test(self):
        t = ProductImage.objects.get(pk=4)
        t.delete()

    def image_tag_test(self):
        t = ProductImage.objects.get(pk=4)
        url = "/image.jpg"
        self.assertEqual(t.image_tag(), u'<img src="{}" style="width: 400px;"/>'.format(url))

class TagTest(TestCase):
    # Tag has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        store = Store.objects.get(pk=1)
        t = Tag.objects.get(name="TestTag")
        self.assertIsNot(t.cg_created_at, None)
        self.assertIsNot(t.cg_updated_at, None)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, "TestTag")
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.store, store)
        self.assertEqual(t.store_id, store.id)
        self.assertIsNone(t.url)

class ContentTest(TestCase):
    # Content has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        store = Store.objects.get(pk=1)
        t = Content.objects.get(pk=6)
        self.assertIsNot(t.cg_created_at, None)
        self.assertIsNot(t.cg_updated_at, None)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.store, store)
        self.assertEqual(t.store_id, store.id)

    def image_tag_test(self):
        t = Content.objects.get(pk=6)
        url = "/content.jpg"
        self.assertEqual(t.image_tag(), u'<img src="{}" style="width: 400px;"/>'.format(url))

    # the update function is broken

    def update_test(self):
        t = Content.objects.get(pk=6)
        self.assertEqual(t.update(), t)
    #     t.update(author="John")

class ImageTest(TestCase):
    # Image has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        store = Store.objects.get(pk=1)
        t = Image.objects.get(pk=6)
        self.assertIsNot(t.cg_created_at, None)
        self.assertIsNot(t.cg_updated_at, None)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.store, store)
        self.assertEqual(t.store_id, store.id)

    def save_test(self):
        t = Image.objects.get(pk=6)
        self.assertIsNone(t.width)
        self.assertIsNone(t.height)
        with self.assertRaises(KeyError):
            self.assertIsNone(t.attributes['sizes'])
        t.save()
        self.assertEqual(t.width, 0)
        self.assertEqual(t.height, 0)

    def save_dimensions_test(self):
        t = Image.objects.get(pk=6)
        t.attributes['sizes'] = {
            "master": {
                "width": 640,
                "height": 480
            }
        }
        self.assertIsNone(t.width)
        self.assertIsNone(t.height)
        self.assertIsNotNone(t.attributes['sizes'])
        t.save()
        self.assertEqual(t.width, 640)
        self.assertEqual(t.height, 480)

    @mock.patch('apps.imageservice.utils.delete_cloudinary_resource', mock.Mock())
    def delete_test(self):
        url = "/content.jpg"
        t = Image.objects.get(pk=6)
        t.delete()


class CategoryTest(TestCase):
    # Category has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        name = "TestCategory"
        store = Store.objects.get(pk=1)
        c = Category.objects.get(name=name)
        self.assertIsNot(c.cg_created_at, None)
        self.assertIsNot(c.cg_updated_at, None)
        self.assertTrue(c.id > 0)
        self.assertIsNone(c.ir_cache)
        self.assertEqual(c.name, name)
        self.assertTrue(c.pk > 0)
        self.assertEqual(c.store, store)
        self.assertEqual(c.store_id, store.id)
        self.assertIsNone(c.url)

    def clean_fields_test(self):
        for i in range(2):
            with self.assertRaises(ValidationError):
                name = "TestCategory"
                store = Store.objects.get(pk=1)
                c = Category.objects.get(name=name)
                c2 = Category.objects.create(name=name, store=store)
                c.clean_fields()

    def clean_fields_same_pk_test(self):
        for i in range(2):
            with self.assertRaises(ValidationError):
                name = "TestCategory"
                store = Store.objects.get(pk=1)
                c = Category.objects.get(name=name)
                c2 = Category.objects.create(name="OtherName", store=store)
                c2.pk = 7
                c2.save()
                c.clean_fields()
        

class PageTest(TestCase):
    # Page has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        name = "TestPage"
        url_slug = "test_page"
        store = Store.objects.get(pk=1)
        p = Page.objects.get(url_slug=url_slug)
        self.assertIsNone(p.campaign)
        self.assertIsNone(p.campaign_id)
        self.assertIsNot(p.cg_created_at, None)
        self.assertIsNot(p.cg_updated_at, None)
        self.assertTrue(p.id > 0)
        self.assertIsNone(p.ir_cache)
        self.assertIsNone(p.last_published_at)
        self.assertIsNone(p.legal_copy)
        self.assertEqual(p.name, name)
        self.assertTrue(p.pk > 0)
        self.assertEqual(p.store, store)
        self.assertEqual(p.store_id, store.id)
        self.assertIsNone(p.theme)
        self.assertIsNone(p.theme_id)
        self.assertIs(type(p.theme_settings), dict)
        self.assertEqual(p.theme_settings_fields, [('image_tile_wide', 0.0), ('desktop_hero_image', ''), ('mobile_hero_image', ''), ('column_width', 256), ('social_buttons', []), ('enable_tracking', 'true')])
        self.assertEqual(p.url_slug, url_slug)

    def deepcopy_test(self):
        name = "TestPage"
        url_slug = "test_page"
        store = Store.objects.get(pk=1)
        p = Page.objects.get(url_slug=url_slug)
        feed = Feed.objects.get(pk=9)
        p.feed = feed # feed must be added for deepcopy to execute
        pp = p.deepcopy()
        self.assertIsNone(pp.campaign)
        self.assertIsNone(pp.campaign_id)
        self.assertIsNot(pp.cg_created_at, None)
        self.assertIsNot(pp.cg_updated_at, None)
        self.assertTrue(pp.id > 0)
        self.assertIsNone(pp.ir_cache)
        self.assertIsNone(pp.last_published_at)
        self.assertIsNone(pp.legal_copy)
        self.assertEqual(pp.name, name)
        self.assertTrue(pp.pk > 0)
        self.assertEqual(pp.feed.tiles.first().template, p.feed.tiles.first().template)
        self.assertEqual(pp.store, store)
        self.assertEqual(pp.store_id, store.id)
        self.assertIsNone(pp.theme)
        self.assertIsNone(pp.theme_id)
        self.assertIs(type(pp.theme_settings), dict)
        self.assertEqual(pp.theme_settings_fields, [('image_tile_wide', 0.0), ('desktop_hero_image', ''), ('mobile_hero_image', ''), ('column_width', 256), ('social_buttons', []), ('enable_tracking', 'true')])
        self.assertEqual(pp.url_slug, "{}_1".format(url_slug))

    def copy_test(self):
        name = "TestPage"
        url_slug = "test_page"
        store = Store.objects.get(pk=1)
        p = Page.objects.get(url_slug=url_slug)
        feed = Feed.objects.get(pk=9)
        p.feed = feed
        pp = p.copy()
        self.assertIsNone(pp.campaign)
        self.assertIsNone(pp.campaign_id)
        self.assertIsNot(pp.cg_created_at, None)
        self.assertIsNot(pp.cg_updated_at, None)
        self.assertTrue(pp.id > 0)
        self.assertIsNone(pp.ir_cache)
        self.assertIsNone(pp.last_published_at)
        self.assertIsNone(pp.legal_copy)
        self.assertEqual(pp.name, name)
        self.assertTrue(pp.pk > 0)
        self.assertEqual(pp.feed, p.feed)
        self.assertEqual(pp.store, store)
        self.assertEqual(pp.store_id, store.id)
        self.assertIsNone(pp.theme)
        self.assertIsNone(pp.theme_id)
        self.assertIs(type(pp.theme_settings), dict)
        self.assertEqual(pp.theme_settings_fields, [('image_tile_wide', 0.0), ('desktop_hero_image', ''), ('mobile_hero_image', ''), ('column_width', 256), ('social_buttons', []), ('enable_tracking', 'true')])
        self.assertEqual(pp.url_slug, "{}_1".format(url_slug))

    def replace_test(self):
        name = "TestPage"
        url_slug = "test_page"
        store = Store.objects.get(pk=1)
        p = Page.objects.get(url_slug=url_slug)
        feed = Feed.objects.get(pk=9)
        p.feed = feed
        pp = Page.objects.get(pk=17)
        pp.replace(p)
        # assure page has been deleted
        with self.assertRaises(ObjectDoesNotExist):
            Page.objects.get(pk=8)
        self.assertIsNone(pp.campaign)
        self.assertIsNone(pp.campaign_id)
        self.assertIsNot(pp.cg_created_at, None)
        self.assertIsNot(pp.cg_updated_at, None)
        self.assertTrue(pp.id > 0)
        self.assertIsNone(pp.ir_cache)
        self.assertIsNone(pp.last_published_at)
        self.assertIsNone(pp.legal_copy)
        self.assertEqual(pp.name, name)
        self.assertTrue(pp.pk > 0)
        self.assertFalse(pp.feed)
        self.assertEqual(pp.store, store)
        self.assertEqual(pp.store_id, store.id)
        self.assertIsNone(pp.theme)
        self.assertIsNone(pp.theme_id)
        self.assertIs(type(pp.theme_settings), dict)
        self.assertEqual(pp.theme_settings_fields, [('image_tile_wide', 0.0), ('desktop_hero_image', ''), ('mobile_hero_image', ''), ('column_width', 256), ('social_buttons', []), ('enable_tracking', 'true')])
        self.assertEqual(pp.url_slug, url_slug)


class FeedTest(TestCase):
    fixtures = ['assets_models.json']

    def properties_test(self):
        store = Store.objects.get(pk=1)
        f = Feed.objects.get(pk=9)
        self.assertIsNot(f.cg_created_at, None)
        self.assertIsNot(f.cg_updated_at, None)
        self.assertTrue(f.id > 0)
        self.assertIsNone(f.ir_cache)
        self.assertEqual(f.store, store)
        self.assertEqual(f.store_id, store.id)

    def find_tiles_content_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        c = Content.objects.get(pk=6)
        t.content.add(c)
        self.assertEqual(set(f.find_tiles(content=c)), set([t]))

    def find_tiles_product_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12)
        t.products.add(p)
        self.assertEqual(set(f.find_tiles(product=p)), set([t]))

    def find_tiles_none_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        self.assertEqual(set(f.find_tiles()), set([t]))

    def find_tiles_no_product_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12)
        self.assertEqual(set(f.find_tiles(product=p)), set([]))

    def find_tiles_no_content_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        c = Content.objects.get(pk=6)
        self.assertEqual(set(f.find_tiles(content=c)), set([]))

    def get_in_stock_tiles_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        self.assertEqual(set(f.get_in_stock_tiles()), set([t]))

    def get_in_stock_tiles_empty_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12)
        p.in_stock = False
        t.products.add(p)
        self.assertEqual(set(f.get_in_stock_tiles()), set([]))

    def get_all_products_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12)
        t.products.add(p)
        self.assertEqual(set(f.get_all_products()), set([p]))

    def get_all_products_no_products_test(self):
        f = Feed.objects.get(pk=9)
        self.assertEqual(set(f.get_all_products()), set([]))

    def test_product_image_add(self):
        f = Feed.objects.get(pk=9)
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        p.default_image = i
        p.product_images.add(i)
        f.add(p)
        self.assertEqual(set(f.get_all_products()), set([p]))

    def generic_test_add(self):
        f = Feed.objects.get(pk=9)
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        p.default_image = i
        p.product_images.add(i)
        f.add(p)
        self.assertEqual(set(f.get_all_products()), set([p]))

    def deepdelete_test(self):
        f = Feed.objects.get(pk=9)
        f._deepdelete_tiles(f.tiles.all())
        self.assertEqual(set(f.get_in_stock_tiles()), set([]))

    @mock.patch('apps.assets.models.Feed._add_product', mock.Mock())
    def only_add_product_test(self):
        f = Feed.objects.get(pk=9)
        p = Product.objects.get(pk=12)
        f.add(p)
        Feed._add_product.assert_called_once_with(product=p, priority=0, category=None, force_create_tile=False)

    @mock.patch('apps.assets.models.Feed._add_content', mock.Mock())
    def only_add_content_test(self):
        f = Feed.objects.get(pk=9)
        c = Content.objects.get(pk=6)
        f.add(c)
        Feed._add_content.assert_called_once_with(content=c, priority=0, category=None, force_create_tile=False)

    @mock.patch('apps.assets.models.Feed._copy_tile', mock.Mock())
    def only_add_tile_test(self):
        f = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        f.add(t)
        Feed._copy_tile.assert_called_once_with(tile=t, priority=0, category=None)

    def add_product_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        f._add_product(p, priority=35, category=cat, force_create_tile=False)
        self.assertEqual(len(f.tiles.all()), 1)
        self.assertEqual(f.tiles.first().product, p)
        self.assertEqual(f.tiles.first().priority, 35)
        self.assertEqual(len(f.tiles.first().categories.all()), 1)
        self.assertEqual(f.tiles.first().categories.first(), cat)

    def add_existing_product_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        # create new tile
        with transaction.atomic():
            with disable_tile_serialization():
                new_tile = Tile(feed=f, template='product', priority=2)
                new_tile.placeholder = p.is_placeholder
                new_tile.get_pk()
                new_tile.products.add(p)
                new_tile.categories.add(cat)
            new_tile.save() # full clean & generate ir_cache
        f._add_product(p, priority=35, category=cat, force_create_tile=False)
        self.assertEqual(len(f.tiles.all()), 1)
        self.assertEqual(f.tiles.first(), new_tile)
        self.assertEqual(f.tiles.first().product, p)
        self.assertEqual(f.tiles.first().priority, 35)
        self.assertEqual(len(f.tiles.first().categories.all()), 1)
        self.assertEqual(f.tiles.first().categories.first(), cat)

    def add_product_force_create_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        # create new tile
        with transaction.atomic():
            with disable_tile_serialization():
                new_tile = Tile(feed=f, template='product', priority=2)
                new_tile.placeholder = p.is_placeholder
                new_tile.get_pk()
                new_tile.products.add(p)
                new_tile.categories.add(cat)
            new_tile.save() # full clean & generate ir_cache
        f._add_product(p, priority=35, category=cat, force_create_tile=True)
        self.assertEqual(len(f.tiles.all()), 2)
        self.assertEqual(f.tiles.first().product, p)
        self.assertEqual(f.tiles.last().product, p)

    def add_content_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        c = Content.objects.get(pk=12)
        f._add_content(c, priority=35, category=cat, force_create_tile=False)
        self.assertEqual(len(f.tiles.all()), 1)
        self.assertEqual(f.tiles.first().content.first(), c)
        self.assertEqual(f.tiles.first().priority, 35)
        self.assertEqual(len(f.tiles.first().categories.all()), 1)
        self.assertEqual(f.tiles.first().categories.first(), cat)

    def add_existing_content_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        p = Content.objects.get(pk=12)
        # create new tile
        with transaction.atomic():
            with disable_tile_serialization():
                new_tile = Tile(feed=f, template='product', priority=2)
                new_tile.placeholder = p.is_placeholder
                new_tile.get_pk()
                new_tile.products.add(p)
                new_tile.categories.add(cat)
            new_tile.save() # full clean & generate ir_cache
        f._add_content(p, priority=35, category=cat, force_create_tile=False)
        self.assertEqual(len(f.tiles.all()), 1)
        self.assertEqual(f.tiles.first(), new_tile)
        self.assertEqual(f.tiles.first().product, p)
        self.assertEqual(f.tiles.first().priority, 35)
        self.assertEqual(len(f.tiles.first().categories.all()), 1)
        self.assertEqual(f.tiles.first().categories.first(), cat)

    def add_content_force_create_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        p = Content.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        # create new tile
        with transaction.atomic():
            with disable_tile_serialization():
                new_tile = Tile(feed=f, template='product', priority=2)
                new_tile.placeholder = p.is_placeholder
                new_tile.get_pk()
                new_tile.products.add(p)
                new_tile.categories.add(cat)
            new_tile.save() # full clean & generate ir_cache
        f._add_content(p, priority=35, category=cat, force_create_tile=True)
        self.assertEqual(len(f.tiles.all()), 2)
        self.assertEqual(f.tiles.first().product, p)
        self.assertEqual(f.tiles.last().product, p)


class TileTest(TestCase):
    # Tile has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        ir_cache = '{"priority": 0, "tagged-products": [], "tile-id": 10, "template": "default"}'
        store = Store.objects.get(pk=1)
        feed = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        self.assertIsNot(t.cg_created_at, None)
        self.assertIsNot(t.cg_updated_at, None)
        self.assertTrue(t.id > 0)
        self.assertEqual(t.ir_cache, ir_cache)
        self.assertEqual(t.feed, feed)

    def clean_no_products_test(self):
        t = Tile.objects.get(pk=10)
        t.clean()
        self.assertTrue(t.in_stock)

    def clean_one_product_test(self):
        p = Product.objects.get(pk=12)
        t = Tile.objects.get(pk=10)
        t.products.add(p)
        t.clean()
        self.assertFalse(t.in_stock)

    def clean_two_product_test(self):
        p1 = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=13)
        t = Tile.objects.get(pk=10)
        t.products.add(p1)
        t.products.add(p2)
        t.clean()
        self.assertTrue(t.in_stock)

    def product_different_store_save_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12)
        store = Store.objects.get(pk=14)
        t.products.add(p)
        p.store = store
        with self.assertRaises(ValidationError):
            p.save()
            t.clean_fields()

    def product_different_store_add_test(self):
        with self.assertRaises(ValidationError):
            p = Product.objects.get(pk=15)
            t = Tile.objects.get(pk=10)
            t.products.add(p)

    def content_different_store_save_test(self):
        t = Tile.objects.get(pk=10)
        c = Content.objects.get(pk=6)
        store = Store.objects.get(pk=14)
        t.content.add(c)
        c.store = store
        with self.assertRaises(ValidationError):
            c.save()
            t.clean_fields()

    def content_different_store_add_test(self):
        with self.assertRaises(ValidationError):
            c = Content.objects.get(pk=16)
            t = Tile.objects.get(pk=10)
            t.content.add(c)
            t.clean_fields()

