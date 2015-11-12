from django.db.models.base import ModelBase
from django.db import models
import mock
import datetime
import time
from unittest import TestCase

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, ProductImage, Feed

"""

We are avoiding fixtures because they are so slow:
http://www.mattjmorrison.com/2011/09/mocking-django.html

"""

class BaseModelTest(TestCase):
    def setUp(self):
        # create a dummy model to inherit abstract class BaseModel
        self.model = ModelBase(BaseModel)

class StoreTest(TestCase):
    # Store has no methods
    def setUp(self):
        self.name = "Test Store"
        self.slug = "test_store"
        self.store = Store.objects.create(name=self.name, slug=self.slug)

    def properties_test(self):
        self.assertEqual(self.store.slug, self.slug)
        self.assertEqual(self.store.name, self.name)
        self.assertIs(type(self.store.cg_created_at), unicode)
        self.assertIs(type(self.store.cg_updated_at), unicode)
        self.assertIs(type(self.store.created_at), datetime.datetime)
        self.assertIs(type(self.store.name), str)
        self.assertIs(type(self.store.pk), int)
        self.assertIs(type(self.store.updated_at), datetime.datetime)

    def tearDown(self):
        self.store.delete()

class ThemeTest(TestCase):
    # Theme has no methods
    def properties_test(self):
        name = "TestTheme{}".format(int(time.time() * 1000) % 1000)
        t = Theme.objects.create(name=name)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.id), int)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, name)
        self.assertIs(type(t.pk), int)
        self.assertTrue(t.pk > 0)
        self.assertIs(type(t.template), unicode)
        self.assertIs(type(t.updated_at), datetime.datetime)

class TagTest(TestCase):
    #Tag has no methods
    def setUp(self):
        self.store = Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        t = Tag.objects.create(name="TestTag", store=self.store)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.created_at), datetime.datetime)
        self.assertIs(type(t.id), int)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, "TestTag")
        self.assertIs(type(t.pk), int)
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.store, self.store)
        self.assertEqual(t.store_id, self.store.id)
        self.assertIsNone(t.url)

    def tearDown(self):
        self.store.delete()

class CategoryTest(TestCase):
    #Category has no methods
    def setUp(self):
        Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        name = "TestCategory"
        s = Store.objects.get(name="TestStore")
        c = Category.objects.create(name=name, store=s)
        self.assertIs(type(c.cg_created_at), unicode)
        self.assertIs(type(c.cg_updated_at), unicode)
        self.assertIs(type(c.created_at), datetime.datetime)
        self.assertTrue(c.id > 0)
        self.assertIsNone(c.ir_cache)
        self.assertEqual(c.name, name)
        self.assertTrue(c.pk > 0)
        self.assertEqual(c.store, s)
        self.assertEqual(c.store_id, s.id)
        self.assertIsNone(c.url)

    def tearDown(self):
        Store.objects.get(name="TestStore").delete()

class PageTest(TestCase):
    #Page has no methods
    def setUp(self):
        self.store = Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        name = "TestPage"
        url_slug = "test_page"
        p = Page.objects.create(name=name, store=self.store, url_slug=url_slug)
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
        self.assertEqual(p.store, self.store)
        self.assertEqual(p.store_id, self.store.id)
        self.assertIsNone(p.theme)
        self.assertIsNone(p.theme_id)
        self.assertIs(type(p.theme_settings), dict)
        self.assertEqual(p.theme_settings_fields, [('image_tile_wide', 0.0), ('desktop_hero_image', ''), ('mobile_hero_image', ''), ('column_width', 256), ('social_buttons', []), ('enable_tracking', 'true')])
        self.assertEqual(p.url_slug, url_slug)

    def tearDown(self):
        self.store.delete()

class ProductTest(TestCase):
    #Product has no methods
    def setUp(self):
        self.store = Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        pprice = 19.99
        p = Product.objects.create(store=self.store, price=pprice)
        self.assertEqual(p.store, self.store)
        self.assertEqual(p.store_id, self.store.id)
        self.assertEqual(p.price, pprice)
        self.assertTrue(p.id > 0)
        self.assertTrue(p.pk > 0)

    def blank_clean_test(self):
        product_config = {'product_images.all.return_value': [],
                          'attributes': None}
        p = mock.Mock(spec=Product)
        p.configure_mock(**product_config)
        Product.clean(p)
        self.assertEqual(p.attributes, {})

    def one_image_clean_test(self):
        image = mock.Mock()
        product_config = {'product_images.all.return_value': [image],
                          'attributes': None,
                          'default_image': None,
                          'product_images.first.return_value': image}
        p = mock.Mock(spec=Product)
        p.configure_mock(**product_config)
        Product.clean(p)
        self.assertEqual(p.default_image, image)

    def tearDown(self):
        self.store.delete()

class ProductImageTest(TestCase):
    #ProductImage has no methods
    def properties_test(self):
        url = "/image.jpg"
        original_url = "test.com/image.jpg"
        product_image = ProductImage.objects.create(url=url, original_url=original_url)
        self.assertIs(type(product_image.cg_created_at), unicode)
        self.assertIs(type(product_image.cg_updated_at), unicode)
        self.assertIs(type(product_image.created_at), datetime.datetime)
        self.assertTrue(product_image.id > 0)
        self.assertIsNone(product_image.ir_cache)
        self.assertTrue(product_image.pk > 0)
        self.assertEqual(product_image.url, url)
        self.assertEqual(product_image.original_url, original_url)

class FeedTest(TestCase):
    #Feed has no methods
    def setUp(self):
        self.store = Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        f = Feed.objects.create(store=self.store)
        self.assertIs(type(f.cg_created_at), unicode)
        self.assertIs(type(f.cg_updated_at), unicode)
        self.assertIs(type(f.created_at), datetime.datetime)
        self.assertTrue(f.id > 0)
        self.assertIsNone(f.ir_cache)
        self.assertIs(type(f.pk), int)
        self.assertTrue(f.pk > 0)
        self.assertEqual(f.store, self.store)
        self.assertEqual(f.store_id, self.store.id)

    def tearDown(self):
        self.store.delete()

class TileTest(TestCase):
    #Tile has no methods
    def setUp(self):
        self.store = Store.objects.create(name="TestStore", slug="test")
        self.feed = Feed.objects.create(store=self.store)

    def properties_test(self):
        t = Tile.objects.create(store=self.store, feed=self.feed)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.created_at), datetime.datetime)
        self.assertTrue(t.id > 0)
        self.assertIsNone(t.ir_cache)
        self.assertIs(type(t.pk), int)
        self.assertTrue(t.pk > 0)
        self.assertEqual(t.store, self.store)
        self.assertEqual(t.store_id, self.store.id)

    def tearDown(self):
        self.store.delete()

