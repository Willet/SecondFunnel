from django.core.management import call_command
from django.db.models.base import ModelBase
from django.db import models, transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
import mock
import datetime
import time
import logging
import itertools
from django.test import TestCase
from django.db.models.signals import post_save, m2m_changed

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
from apps.imageservice.utils import delete_cloudinary_resource, delete_s3_resource
from apps.assets.utils import disable_tile_serialization
import apps.intentrank.serializers as ir_serializers

from apps.assets.signals import content_m2m_changed, content_saved, product_saved, \
                                productimage_saved, tile_m2m_changed, tile_saved

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

    def init_image_sizes_dict_test(self):
        sizes = {
            "master": {
                "width": 640,
                "height": 480,
                "url": "http://images.secondfunnel.com/foo/bar.jpg",
            },
            "w400": {
                "width": 400,
                "height": 400,
                "url": "http://images.secondfunnel.com/foo/w400/bar.jpg",
            },
            "h400": {
                "height": 400,
                "url": "http://images.secondfunnel.com/foo/h400/bar.jpg",
            }
        }
        pi = ProductImage(
                product=Product.objects.get(pk=3),
                original_url="http://www.google.com/foo/bar.jpg",
                image_sizes=sizes,
                dominant_color="#FFFFFF",
                url="http://images.secondfunnel.com/foo/bar.jpg",
                file_type="jpg")
        self.assertEqual(len(pi.image_sizes), 3)
        self.assertTrue("master" in pi.image_sizes)
        self.assertTrue("w400" in pi.image_sizes)
        self.assertTrue("h400" in pi.image_sizes)
        self.assertNotEqual(pi.image_sizes.find({"height": 400}), (None, None))
        self.assertEqual(pi.image_sizes.find({"height": 500}), (None, None))

    def save_test(self):
        t = ProductImage.objects.get(pk=4)
        self.assertIsNone(t.width)
        self.assertIsNone(t.height)
        self.assertEqual(len(t.image_sizes), 0)
        t.save()
        self.assertEqual(t.width, 0)
        self.assertEqual(t.height, 0)

    def save_dimensions_test(self):
        t = ProductImage.objects.get(pk=4)
        t.image_sizes["master"] = {
            "width": 640,
            "height": 480
        }
        self.assertIsNone(t.width)
        self.assertIsNone(t.height)
        self.assertIsNotNone(t.image_sizes['master'])
        t.save()
        self.assertEqual(t.width, 640)
        self.assertEqual(t.height, 480)
        self.assertEqual(t.orientation, "landscape")

    @mock.patch('apps.assets.models.delete_resource')
    def delete_dev_test(self, mock_delete_resource):
        # No remote resources deleted from dev
        with mock.patch('django.conf.settings.ENVIRONMENT', 'dev'):
            pi = ProductImage.objects.get(pk=11)
            with mock.patch.object(pi.image_sizes, 'delete_resources'):
                pi.delete()
                mock_delete_resource.assert_not_called()
                pi.image_sizes.delete_resources.assert_not_called()
                with self.assertRaises(ObjectDoesNotExist):
                    pi = ProductImage.objects.get(pk=11)

    @mock.patch('apps.assets.models.delete_resource')
    def delete_stage_test(self, mock_delete_resource):
        # No remote resources deleted from stage
        with mock.patch('django.conf.settings.ENVIRONMENT', 'stage'):
            pi = ProductImage.objects.get(pk=11)
            with mock.patch.object(pi.image_sizes, 'delete_resources'):
                pi.delete()
                mock_delete_resource.assert_not_called()
                pi.image_sizes.delete_resources.assert_not_called()
                with self.assertRaises(ObjectDoesNotExist):
                    pi = ProductImage.objects.get(pk=11)

    @mock.patch('apps.assets.models.delete_resource')
    def delete_production_test(self, mock_delete_resource):
        # Url & image size remote resources deleted on production
        with mock.patch('django.conf.settings.ENVIRONMENT', 'production'):
            pi = ProductImage.objects.get(pk=11)
            with mock.patch.object(pi.image_sizes, 'delete_resources'):
                pi.delete()
                mock_delete_resource.assert_called_once_with(pi.url)
                pi.image_sizes.delete_resources.assert_called_once_with()
                with self.assertRaises(ObjectDoesNotExist):
                    pi = ProductImage.objects.get(pk=11)


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

    def find_tiles_test(self):
        f = Feed.objects.get(pk=13)
        t = Tile.objects.get(pk=13)
        self.assertTrue(t.feed == f)
        self.assertEqual(set(f.find_tiles()), set([t]))

    def find_tiles_content_test(self):
        f = Feed.objects.get(pk=13)
        t = Tile.objects.get(pk=13)
        c = Content.objects.get(pk=6)
        t.content.add(c)
        self.assertTrue(t.feed == f)
        self.assertEqual(set(f.find_tiles(content=c)), set([t]))

    def find_tiles_product_test(self):
        f = Feed.objects.get(pk=13)
        t = Tile.objects.get(pk=13)
        p = Product.objects.get(pk=12)
        t.products.add(p)
        self.assertTrue(t.feed == f)
        self.assertEqual(set(f.find_tiles(product=p)), set([t]))

    def find_tiles_none_test(self):
        f = Feed.objects.get(pk=19)
        self.assertTrue(f.tiles.count() == 0)
        self.assertTrue(len(f.find_tiles()) == 0)

    def find_tiles_no_product_test(self):
        f = Feed.objects.get(pk=13)
        t = Tile.objects.get(pk=13)
        p = Product.objects.get(pk=12)
        self.assertTrue(t.feed == f)
        self.assertTrue(f.tiles.count() == 1)
        self.assertTrue(t.products.count() == 0)
        self.assertEqual(set(f.find_tiles(product=p)), set([]))

    def find_tiles_no_content_test(self):
        f = Feed.objects.get(pk=13)
        t = Tile.objects.get(pk=13)
        c = Content.objects.get(pk=6)
        self.assertTrue(t.feed == f)
        self.assertTrue(f.tiles.count() == 1)
        self.assertTrue(t.content.count() == 0)
        self.assertEqual(set(f.find_tiles(content=c)), set([]))

    def get_in_stock_tiles_test(self):
        f = Feed.objects.get(pk=9)
        t1 = Tile.objects.get(pk=10)
        t2 = Tile.objects.get(pk=11)
        p1 = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=13)
        t1.products = [p1]
        t2.products = [p2]
        self.assertFalse(p1.in_stock)
        self.assertTrue(p2.in_stock)
        self.assertTrue(t1.feed == f)
        self.assertTrue(t2.feed == f)
        self.assertEqual(set(f.get_in_stock_tiles()), set([t2]))

    def get_in_stock_tiles_empty_test(self):
        f = Feed.objects.get(pk=13)
        t = Tile.objects.get(pk=13)
        p = Product.objects.get(pk=12)
        t.products.add(p)
        self.assertFalse(p.in_stock)
        self.assertTrue(t.feed == f)
        self.assertTrue(f.tiles.count() == 1)
        self.assertEqual(set(f.get_in_stock_tiles()), set([]))

    def get_all_products_test(self):
        f = Feed.objects.get(pk=13)
        t = Tile.objects.get(pk=13)
        p = Product.objects.get(pk=13) # in stock
        t.products.add(p)
        self.assertTrue(t.feed == f)
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

    def categories_test(self):
        # property gets all cateogries
        f = Feed.objects.get(pk=9)
        c1 = Category.objects.get(pk=7)
        c2 = Category.objects.get(pk=8)
        t1 = Tile.objects.get(pk=10)
        t2 = Tile.objects.get(pk=11)
        c1.tiles.add(t1)
        c2.tiles.add(t2)
        self.assertTrue(t1.feed == f)
        self.assertTrue(t2.feed == f)
        self.assertTrue(set([c1, c2]) == set(f.categories))

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

    # Tests for healthcheck
    
    # Returns Error
    def health_check_error_test(self):
        placeholder_count = 100
        instock_count = 50
        outstock_count = 850
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as categories_patch:
                qs_mock = mock.Mock()
                qs_mock.count.return_value = 1000
                
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                categories_patch.return_value = categories_patch
                categories_patch.tiles.return_value = qs_mock

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10%"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                })

    def health_check_error1_test(self):
        placeholder_count = 1
        instock_count = 8
        outstock_count = 5
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as categories_patch:
                qs_mock = mock.Mock()
                qs_mock.count.return_value = 1000
                
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                categories_patch.return_value = categories_patch
                categories_patch.tiles.return_value = qs_mock

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                })

    def health_check_error2_test(self):
        placeholder_count = 1
        instock_count = 1
        outstock_count = 10
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as categories_patch:
                qs_mock = mock.Mock()
                qs_mock.count.return_value = 1000
                
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                categories_patch.return_value = categories_patch
                categories_patch.tiles.return_value = qs_mock

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10\nIn-stock count < 10%"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                })

    # Returns a Warning
    def health_check_warning_test(self):
        placeholder_count = 100
        instock_count = 200
        outstock_count = 700
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as categories_patch:
                qs_mock = mock.Mock()
                qs_mock.count.return_value = 1000
                
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                categories_patch.return_value = categories_patch
                categories_patch.tiles.return_value = qs_mock

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('WARNING', u"In-stock count is between 10% and 30%"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                })

    # Returns an OK
    def health_check_ok_test(self):
        placeholder_count = 100
        instock_count = 500
        outstock_count = 400
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as categories_patch:
                qs_mock = mock.Mock()
                qs_mock.count.return_value = 1000
                
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                categories_patch.return_value = categories_patch
                categories_patch.tiles.return_value = qs_mock

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('OK', u"In-stock count is greater than 30%"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                })

    # Normally returns an OK but changed to error + error messages due to categories.tiles < 10
    def health_check_ok_error_test(self):
        placeholder_count = 100
        instock_count = 600
        outstock_count = 300
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 5
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 10
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 8
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"Category 'cat1' only has 5 in-stock tiles\nCategory 'cat3' only has 8 in-stock tiles"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

   # Normally returns an OK but changed to error + error messages due to instock_count < 10
    def health_check_ok_error1_test(self):
        placeholder_count = 1
        instock_count = 5
        outstock_count = 4
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 11
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 10
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 11
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

   # Normally returns an OK but changed to error + error messages due to instock_count < 10 and categories in_stock < 10
    def health_check_ok_error2_test(self):
        placeholder_count = 1
        instock_count = 5
        outstock_count = 4
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 5
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 10
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 8
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10\nCategory 'cat1' only has 5 in-stock tiles\nCategory 'cat3' only has 8 in-stock tiles"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

    # Normally returns an warning but changed to error + error messages due to categories.tiles < 10
    def health_check_warning_error_test(self):
        placeholder_count = 100
        instock_count = 200
        outstock_count = 700
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 5
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 10
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 8
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"Category 'cat1' only has 5 in-stock tiles\nCategory 'cat3' only has 8 in-stock tiles"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

    # Normally returns an warning but changed to error + error messages due to in-stock < 10
    def health_check_warning_error1_test(self):
        placeholder_count = 1
        instock_count = 5
        outstock_count = 3
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 5
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 10
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 8
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10\nCategory 'cat1' only has 5 in-stock tiles\nCategory 'cat3' only has 8 in-stock tiles"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

    # Normally returns an error, + error messages due to categories.tiles < 10
    def health_check_error_error_test(self):
        placeholder_count = 100
        instock_count = 50
        outstock_count = 850
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 5
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 8
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 8
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10%\nCategory 'cat1' only has 5 in-stock tiles\nCategory 'cat2' only has 8 in-stock tiles\nCategory 'cat3' only has 8 in-stock tiles"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

    # Normally returns an error, + error messages due to in-stock count < 10
    def health_check_error_error1_test(self):
        placeholder_count = 1
        instock_count = 3
        outstock_count = 90
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 11
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 12
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 13
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10\nIn-stock count < 10%"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

    # Normally returns an error, + error messages due to in-stock count < 10 and categories.tile < 10
    def health_check_error_error2_test(self):
        placeholder_count = 7
        instock_count = 3
        outstock_count = 90
        total_count = placeholder_count + instock_count + outstock_count

        def filter_side_effect(*args, **kwargs):
            mocked = mock.Mock()
            if kwargs['placeholder'] == True:
                mocked.count.return_value = placeholder_count
            elif kwargs['in_stock'] == True:
                mocked.count.return_value = instock_count
            else:
                mocked.count.return_value = outstock_count
            return mocked

        cat1 = mock.Mock()
        cat1.name = "cat1"
        cat1.tiles.filter.return_value.count.return_value = 5
        cat2 = mock.Mock()
        cat2.name = "cat2"
        cat2.tiles.filter.return_value.count.return_value = 8
        cat3 = mock.Mock() 
        cat3.name = "cat3"
        cat3.tiles.filter.return_value.count.return_value = 8
        cat_list = [cat1, cat2, cat3]

        def fake_categories(ind):
            return cat_list[ind]

        with mock.patch('apps.assets.models.Feed.tiles') as tile_patch:
            with mock.patch('apps.assets.models.Feed.categories') as feed_cat_patch:
                tile_patch.count.return_value = total_count
                tile_patch.filter.side_effect = filter_side_effect
                feed_cat_patch.__iter__.return_value = cat_list
                feed_cat_patch.__getitem__.side_effect = fake_categories

                f = Feed.objects.get(pk=9)
                results = f.healthcheck()
                self.assertEqual(results,{
                        'status': ('ERROR', u"In-stock count < 10\nIn-stock count < 10%\nCategory 'cat1' only has 5 in-stock tiles\nCategory 'cat2' only has 8 in-stock tiles\nCategory 'cat3' only has 8 in-stock tiles"), 
                        'results': {'in_stock': instock_count, 'placeholder': placeholder_count, 'out_of_stock': outstock_count}
                    })

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

