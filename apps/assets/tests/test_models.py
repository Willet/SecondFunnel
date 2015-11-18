from django.core.management import call_command
from django.db.models.base import ModelBase
from django.db import models
import mock
import datetime
import time
import factory
from decimal import *
from django.test import TestCase

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content

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
        print self.store.id
        self.assertEqual(self.store.slug, "store_slug")
        self.assertEqual(self.store.name, "MyStore")
        self.assertIs(type(self.store.cg_created_at), unicode)
        self.assertIs(type(self.store.cg_updated_at), unicode)
        self.assertIs(type(self.store.created_at), datetime.datetime)
        self.assertTrue(self.store.id > 0)
        self.assertIs(type(self.store.name), unicode)
        self.assertIs(type(self.store.pk), int)
        self.assertIs(type(self.store.updated_at), datetime.datetime)

class ThemeTest(TestCase):
    # Theme has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        t = Theme.objects.get(pk=2)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.id), int)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, "Default")
        self.assertIs(type(t.pk), int)
        self.assertTrue(t.pk > 0)
        self.assertIs(type(t.template), unicode)
        self.assertIs(type(t.updated_at), datetime.datetime)

class ProductTest(TestCase):
    # Product has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        pprice = 19.99
        store_id = 1
        p = Product.objects.get(pk=3)
        self.assertEqual(p.store_id, store_id)
        self.assertEqual(float(p.price), pprice)
        self.assertTrue(p.id > 0)
        self.assertTrue(p.pk > 0)

    def blank_clean_test(self):
        p = Product.objects.get(pk=3)
        p.clean
        self.assertEqual(p.attributes, {})

    def one_image_clean_test(self):
        p = Product.objects.get(pk=3)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        Product.clean(p)
        self.assertEqual(p.default_image, i)

class ProductImageTest(TestCase):
    # ProductImage has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        url = "/image.jpg"
        original_url = "test.com/image.jpg"
        product_image = ProductImage.objects.get(pk=4)
        self.assertIs(type(product_image.cg_created_at), unicode)
        self.assertIs(type(product_image.cg_updated_at), unicode)
        self.assertIs(type(product_image.created_at), datetime.datetime)
        self.assertTrue(product_image.id > 0)
        self.assertIsNone(product_image.ir_cache)
        self.assertTrue(product_image.pk > 0)
        self.assertEqual(product_image.url, url)
        self.assertEqual(product_image.original_url, original_url)

class TagTest(TestCase):
    # Tag has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        store = Store.objects.get(pk=1)
        t = Tag.objects.get(name="TestTag")
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.created_at), datetime.datetime)
        self.assertIs(type(t.id), int)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, "TestTag")
        self.assertIs(type(t.pk), int)
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
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.created_at), datetime.datetime)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertIs(type(t.pk), int)
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.store, store)
        self.assertEqual(t.store_id, store.id)

class ImageTest(TestCase):
    # Image has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        store = Store.objects.get(pk=1)
        t = Image.objects.get(pk=6)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.created_at), datetime.datetime)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertIs(type(t.pk), int)
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.store, store)
        self.assertEqual(t.store_id, store.id)

class CategoryTest(TestCase):
    # Category has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        name = "TestCategory"
        store = Store.objects.get(pk=1)
        c = Category.objects.get(name=name)
        self.assertIs(type(c.cg_created_at), unicode)
        self.assertIs(type(c.cg_updated_at), unicode)
        self.assertIs(type(c.created_at), datetime.datetime)
        self.assertTrue(c.id > 0)
        self.assertIsNone(c.ir_cache)
        self.assertEqual(c.name, name)
        self.assertTrue(c.pk > 0)
        self.assertEqual(c.store, store)
        self.assertEqual(c.store_id, store.id)
        self.assertIsNone(c.url)

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
        self.assertIs(type(p.cg_created_at), unicode)
        self.assertIs(type(p.cg_updated_at), unicode)
        self.assertIs(type(p.created_at), datetime.datetime)
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

class FeedTest(TestCase):
    # Feed has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        store = Store.objects.get(pk=1)
        f = Feed.objects.get(pk=9)
        self.assertIs(type(f.cg_created_at), unicode)
        self.assertIs(type(f.cg_updated_at), unicode)
        self.assertIs(type(f.created_at), datetime.datetime)
        self.assertTrue(f.id > 0)
        self.assertIsNone(f.ir_cache)
        self.assertIs(type(f.pk), int)
        self.assertTrue(f.pk > 0)
        self.assertEqual(f.store, store)
        self.assertEqual(f.store_id, store.id)

class TileTest(TestCase):
    # Tile has no methods
    fixtures = ['assets_models.json']

    def properties_test(self):
        ir_cache = '{"priority": 0, "tagged-products": [], "tile-id": 10, "template": "default"}'
        store = Store.objects.get(pk=1)
        feed = Feed.objects.get(pk=9)
        t = Tile.objects.get(pk=10)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.created_at), datetime.datetime)
        self.assertTrue(t.id > 0)
        self.assertEqual(t.ir_cache, ir_cache)
        self.assertIs(type(t.pk), int)
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.feed, feed)

