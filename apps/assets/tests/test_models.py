from django.db.models.base import ModelBase
from apps.intentrank.serializers.pages import StoreSerializer
import mock
import datetime
import time
from unittest import TestCase

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page

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
        Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        s = Store.objects.get(name="TestStore")
        self.assertEqual(s.slug, "test")
        self.assertIs(type(s.cg_created_at), unicode)
        self.assertIs(type(s.cg_updated_at), unicode)
        self.assertIs(type(s.created_at), datetime.datetime)
        self.assertIs(type(s.name), unicode)
        self.assertIs(type(s.pk), int)
        self.assertIs(type(s.updated_at), datetime.datetime)

    def tearDown(self):
        Store.objects.get(name="TestStore").delete()

class ThemeTest(TestCase):
    # Theme has no methods
    def properties_test(self):
        name = "TestTheme{}".format(int(time.time() * 1000) % 1000)
        t = Theme.objects.create(name=name)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.id), int)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, name)
        self.assertIs(type(t.pk), int)
        self.assertIs(type(t.template), unicode)
        self.assertIs(type(t.updated_at), datetime.datetime)

class TagTest(TestCase):
    #Tag has no methods
    def setUp(self):
        Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        s = Store.objects.get(name="TestStore")
        t = Tag.objects.create(name="TestTag", store=s)
        self.assertIs(type(t.cg_created_at), unicode)
        self.assertIs(type(t.cg_updated_at), unicode)
        self.assertIs(type(t.created_at), datetime.datetime)
        self.assertIs(type(t.id), int)
        self.assertIsNone(t.ir_cache)
        self.assertEqual(t.name, "TestTag")
        self.assertIs(type(t.pk), int)
        self.assertEqual(t.store, s)
        self.assertEqual(t.store_id, s.id)
        self.assertIsNone(t.url)

    def tearDown(self):
        Store.objects.get(name="TestStore").delete()

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
        self.assertIs(type(c.id), int)
        self.assertIsNone(c.ir_cache)
        self.assertEqual(c.name, name)
        self.assertIs(type(c.pk), int)
        self.assertEqual(c.store, s)
        self.assertEqual(c.store_id, s.id)
        self.assertIsNone(c.url)

    def tearDown(self):
        Store.objects.get(name="TestStore").delete()

class PageTest(TestCase):
    #Page has no methods
    def setUp(self):
        Store.objects.create(name="TestStore", slug="test")

    def properties_test(self):
        name = "TestPage"
        url_slug = "test_page"
        s = Store.objects.get(name="TestStore")
        p = Page.objects.create(name=name, store=s, url_slug=url_slug)
        self.assertIsNone(p.campaign)
        self.assertIsNone(p.campaign_id)
        self.assertIs(type(p.cg_created_at), unicode)
        self.assertIs(type(p.cg_updated_at), unicode)
        self.assertIs(type(p.created_at), datetime.datetime)
        self.assertIs(type(p.id), int)
        self.assertIsNone(p.ir_cache)
        self.assertIsNone(p.last_published_at)
        self.assertIsNone(p.legal_copy)
        self.assertEqual(p.name, name)
        self.assertIs(type(p.pk), int)
        self.assertEqual(p.store, s)
        self.assertEqual(p.store_id, s.id)
        self.assertIsNone(p.theme)
        self.assertIsNone(p.theme_id)
        self.assertIs(type(p.theme_settings), dict)
        self.assertEqual(p.theme_settings_fields, [('image_tile_wide', 0.0), ('desktop_hero_image', ''), ('mobile_hero_image', ''), ('column_width', 256), ('social_buttons', []), ('enable_tracking', 'true')])
        self.assertEqual(p.url_slug, url_slug)

    def tearDown(self):
        Store.objects.get(name="TestStore").delete()
