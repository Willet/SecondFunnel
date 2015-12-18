from django.core.management import call_command
from django.db.models.base import ModelBase
from django.db import models, transaction, connection
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
import mock
import datetime
import time
import factory
import logging
import itertools
from django.test import TestCase
from django.db.models.signals import post_save, m2m_changed
from django.conf import settings

import apps.assets
from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
from apps.imageservice.utils import delete_cloudinary_resource, delete_s3_resource
from apps.assets.utils import disable_tile_serialization
import apps.intentrank.serializers as ir_serializers

from apps.assets.signals import content_m2m_changed, content_saved, product_saved, \
                                productimage_saved, tile_m2m_changed, tile_saved

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

# class ModelMixinTestCase(TestCase):
#     def setUp(self):
#         self.model = ModelBase('__TestModel__'+self.mixin.__name__, (self.mixin,),
#             {'__module__': self.mixin.__module__})

#         # not sure if this is used?
#         # self._style = no_style()
#         sql, _ = connection.creation.sql_create_model(self.model, self._style)

#         self._cursor = connection.cursor()
#         for statement in sql:
#             self._cursor.execute(statement)

#     def tearDown(self):
#         # Delete the schema for the test model
#         sql = connection.creation.sql_destroy_model(self.model, (), self._style)
#         for statement in sql:
#             self._cursor.execute(statement)

# class ExtraModelsTestCase(TestCase):
#     # Change to True if using South for DB migrations and migrating during tests
#     south_migrate = False
#     def _pre_setup(self):
#         # Add the models to the db.
#         self._original_installed_apps = list(settings.INSTALLED_APPS)
#         loading.cache.loaded = False
#         call_command('syncdb', interactive=False, migrate=south_migrate, verbosity=0)
#         # Call the original method that does the fixtures etc.
#         super(TestCase, self)._pre_setup()
#         # Prepare Factories for any of the extra models
#         try:
#             for extra_model in self.extra_models:
#                 # create Factory class for extra_model accessible under {{ extra_model }}Factory name
#                 factory_class = '%sFactory' % extra_model.__name__
#                 cls = type(factory_class, (factory.django.DjangoModelFactory,), dict(FACTORY_FOR=extra_model))
#                 setattr(self, factory_class, cls)
#         except AttributeError:
#             pass
 
#     def _post_teardown(self):
#         # Call the original method.
#         super(TestCase, self)._post_teardown()
#         # Restore the settings.
#         settings.INSTALLED_APPS = self._original_installed_apps

# class TestModel(ModelBase):
#     pass


# class TestModelTestCase(ExtraModelsTestCase):
#     extra_models = (TestModel)
 
#     def test_abstract(self):
#         self.instance = self.TestModelFactory.create()
#         self.assertTrue(self.instance.test_method())

class BaseModelTest(TestCase):
    fixtures = ['assets_models.json']

    def bm_copy_test(self):
        b = Store.objects.get(pk=1)
        b.random_field = "random value"
        result = b._copy(b)
        self.assertEqual(result["name"], "MyStore")
        self.assertEqual(result["description"], "")
        self.assertEqual(result["slug"], "store_slug")
        self.assertEqual(result["default_theme"], None)
        self.assertEqual(result["default_page"], None)
        self.assertEqual(result["public_base_url"], "http://gifts.mystore.com")
        self.assertEqual(result["random_field"], None) # not changed
        self.assertNotEqual(result.pk, b.pk)

    def bm_replace_relations_test(self):
        # for merging products
        b = Product.objects.get(pk=3)
        o = Product.objects.get(pk=12)
        b.similar_products.add(o)
        b._replace_relations([o])
        # should undo similar_products.add
        self.assertEqual(len(b.similar_products.all()), 1)
        self.assertEqual(b.similar_products.first(), b)

    def update_ir_cache_test(self):
        b = Store.objects.get(pk=1)
        old_ir_cache = b.ir_cache # = None, FYI
        with mock.patch('apps.assets.models.Store.to_str', autospec=True) as mocked_handler:
            b.update_ir_cache()
            self.assertEquals(mocked_handler.call_count, 1)
        self.assertEqual(type(b.ir_cache), mock.MagicMock)

    def update_or_create_test(self):
        b = Store.objects.get(pk=1)
        obj, created, updated = b.update_or_create(pk=1)
        self.assertEqual(obj, b)
        self.assertEqual(created, False)
        self.assertEqual(updated, False)

    def get_test(self):
        b = Store.objects.get(pk=1)
        self.assertEqual(b.get("name"), "MyStore")
        self.assertIsNone(b.get("nothing"))
        # raise Exception()


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

    def blank_clean_fields_test(self):
        p = Product.objects.get(pk=3)
        p.price = None
        p.clean_fields()
        self.assertFalse(p.price)

    def type_clean_fields_test(self):
        price = 19.99
        p = Product.objects.get(pk=3)
        p.clean_fields()
        self.assertNotEqual(p.price, price) # price should be converted to float

    def error_clean_fields_test(self):
        with self.assertRaises(ValidationError):
            p = Product.objects.get(pk=3)
            p.price = "Error"
            p.clean_fields()

    def exclude_clean_fields_test(self):
        # test passes if it doesn't throw an exception
        p = Product.objects.get(pk=3)
        p.price = "Error"
        p.clean_fields(["price"])

    def merge_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        i = ProductImage.objects.get(pk=4)
        p2.product_images.add(i)
        p.merge([p2])
        # assure product has been deleted
        with self.assertRaises(ObjectDoesNotExist):
            Product.objects.get(pk=13)


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
        with self.assertRaises(ObjectDoesNotExist):
            t = ProductImage.objects.get(pk=4)

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

    # the update function is broken

    def update_test(self):
        t = Content.objects.get(pk=6)
        self.assertEqual(t.update(), t)
        # if the update function was not broken, we would also test this:
        # t.update(author="John")

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

    # delete_cloudinary_resource is called anytime we delete an Image
    @mock.patch('apps.imageservice.utils.delete_cloudinary_resource', mock.Mock())
    def delete_test(self):
        url = "/content.jpg"
        t = Image.objects.get(pk=6)
        t.delete()
        with self.assertRaises(ObjectDoesNotExist):
            Image.objects.get(pk=6)


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
                # categories can't have the same name
                name = "TestCategory"
                store = Store.objects.get(pk=1)
                c = Category.objects.get(name=name)
                c2 = Category.objects.create(name=name, store=store)
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
        self.assertEqual(pp.url_slug, url_slug)

    def page_get_incremented_url_slug_test(self):
        p = Page.objects.get(pk=8)
        slug = "test_page"
        self.assertEqual(p._get_incremented_url_slug(), "{}_1".format(slug))
        p.url_slug = "{}_1".format(slug)
        p.save()
        self.assertEqual(p._get_incremented_url_slug(), "{}_2".format(slug))

    def page_get_incremented_name_test(self):
        p = Page.objects.get(pk=8)
        page_name = "TestPage"
        self.assertEqual(p._get_incremented_name(), "{} COPY 1".format(page_name))
        p.name = "{} COPY 1".format(page_name)
        p.save()
        self.assertEqual(p._get_incremented_name(), "{} COPY 2".format(page_name))

    @mock.patch('apps.assets.models.Feed.add', mock.Mock())
    def add_alias_test(self):
        p = Page.objects.get(pk=8)
        f = Feed.objects.get(pk=9)
        p.feed = f
        p.save()
        p.add() # call triggered
        Feed.add.assert_called_once_with()

    @mock.patch('apps.assets.models.Feed.remove', mock.Mock())
    def remove_alias_test(self):
        p = Page.objects.get(pk=8)
        f = Feed.objects.get(pk=9)
        p.feed = f
        p.save()
        p.remove() # call triggered
        Feed.remove.assert_called_once_with()


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

    # These tests make sure the correct subfunction is called when .add() is called

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

    # these are the actual sub-function tests

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
        c = Content.objects.get(pk=6)
        f._add_content(c, priority=35, category=cat, force_create_tile=False)
        self.assertEqual(len(f.tiles.all()), 1)
        self.assertEqual(f.tiles.first().content.first(), c)
        self.assertEqual(f.tiles.first().priority, 35)
        self.assertEqual(len(f.tiles.first().categories.all()), 1)
        self.assertEqual(f.tiles.first().categories.first(), cat)

    def add_existing_content_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        c = Content.objects.get(pk=6)
        # create new tile
        with transaction.atomic():
            with disable_tile_serialization():
                new_tile = Tile(feed=f, template='content', priority=2)
                new_tile.placeholder = False
                new_tile.get_pk()
                new_tile.content.add(c)
                new_tile.categories.add(cat)
            new_tile.save() # full clean & generate ir_cache
        f._add_content(c, priority=35, category=cat, force_create_tile=False)
        self.assertEqual(len(f.tiles.all()), 1)
        self.assertEqual(f.tiles.first(), new_tile)
        self.assertEqual(f.tiles.first().content.first(), c)
        self.assertEqual(f.tiles.first().priority, 35)
        self.assertEqual(len(f.tiles.first().categories.all()), 1)
        self.assertEqual(f.tiles.first().categories.first(), cat)

    def add_content_force_create_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        p = Content.objects.get(pk=6)
        # create new tile
        with transaction.atomic():
            with disable_tile_serialization():
                new_tile = Tile(feed=f, template='content', priority=2)
                new_tile.placeholder = False
                new_tile.get_pk()
                new_tile.content.add(p)
                new_tile.categories.add(cat)
            new_tile.save() # full clean & generate ir_cache
        f._add_content(p, priority=35, category=cat, force_create_tile=True)
        self.assertEqual(len(f.tiles.all()), 2)
        self.assertEqual(f.tiles.first().content.first(), p)
        self.assertEqual(f.tiles.last().content.first(), p)

    def add_copy_tile_test(self):
        cat = Category.objects.get(pk=7)
        f = Feed.objects.get(pk=18)
        t = Tile.objects.get(pk=10)
        f._copy_tile(t, priority=35, category=cat)
        self.assertEqual(len(f.tiles.all()), 1)
        # most functionality is in Tile._copy


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

    def tile_copy_test(self):
        t = Tile.objects.get(pk=10)
        f = Feed.objects.get(pk=19)
        with self.assertRaises(ValueError):
            t._copy(update_fields={'feed':f}) # wrong store
        tt = t._copy()
        self.assertEqual(t.template, tt.template)

    def tile_attribute_copy_test(self):
        t = Tile.objects.get(pk=10)
        i = Content.objects.get(pk=6)
        f = Feed.objects.get(pk=19)
        template = "banner"
        tt = t._copy(update_fields={'template': template, "attributes": {"redirect_url": 'example.com'}, "content": [i]})
        self.assertEqual(template, tt.template)
        self.assertNotEqual(t.template, tt.template)

    def deepdelete_test(self):
        t = Tile.objects.get(pk=10)
        i = Content.objects.get(pk=6)
        t.content.add(i)
        t.deepdelete()
        with self.assertRaises(ObjectDoesNotExist):
            Content.objects.get(pk=6)
        with self.assertRaises(ObjectDoesNotExist):
            Tile.objects.get(pk=10)

    def to_json_test(self):
        t = Tile.objects.get(pk=10)
        self.assertEqual(type(t.to_json()), dict)

    @mock.patch('apps.assets.models.Tile._to_str', mock.Mock())
    def to_json_calls(self):
        t = Tile.objects.get(pk=10)
        t.to_json()
        Tile.to_string.assert_called_once_with()

    @mock.patch('apps.intentrank.serializers.DefaultTileSerializer.to_str', mock.Mock())
    def tile_to_string_test(self):
        t = Tile.objects.get(pk = 10)
        t.to_str(skip_cache=False) # mock called
        ir_serializers.DefaultTileSerializer.to_str.assert_called_once_with([t], skip_cache=False)

    def get_first_content_of_test(self):
        t = Tile.objects.get(pk=10)
        c = Content.objects.get(pk=6)
        t.content.add(c)
        self.assertEqual(c, t.get_first_content_of(Content))

    def get_first_content_of_test(self):
        t = Tile.objects.get(pk=10)
        with self.assertRaises(LookupError):
            t.get_first_content_of(Content)

