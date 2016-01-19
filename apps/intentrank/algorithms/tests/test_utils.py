from django.test import TestCase
import mock
import logging
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.query import QuerySet

from apps.utils.functional import may_be_json
from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
import apps.intentrank.serializers as ir_serializers
from apps.intentrank.serializers.utils import SerializerError
from apps.intentrank.algorithms.ir_magic import TemplateRatioEqualizer, TileRatioContainer
import apps.intentrank.algorithms as algorithms
from apps.intentrank.algorithms.utils import qs_for

class IRFilterTest(TestCase):
    fixtures = ['assets_models.json']

    def filter_tiles_test(self):
        f = Feed.objects.get(pk=9) # has 2 in stock tiles
        tiles = list(f.tiles.all()) # force load
        result = algorithms.ir_filter(feed=f)
        self.assertTrue(set(tiles) == set(result))

    def filter_feed_test(self):
        f = Feed.objects.get(pk=9) # has 2 in stock tiles
        tiles = list(f.tiles.all()) # force load
        result = algorithms.ir_filter(feed=f)
        self.assertTrue(set(tiles) == set(result))

    def filter_tiles_from_feed_test(self):
        f = Feed.objects.get(pk=9) # has 2 in stock tiles
        tiles = list(f.tiles.all()) # force load
        p = Product.objects.get(pk=3) # in stock product
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        f.add(p)
        # only tiles will be used b/c they are specifically specified
        result = algorithms.ir_filter(tiles=tiles, feed=f)
        self.assertTrue(set(tiles) == set(result))

    def filter_out_of_stock_test(self):
        f = Feed.objects.get(pk=9) # has 2 in stock tiles
        tiles = list(f.tiles.all()) # force load
        p = Product.objects.get(pk=12) # out of stock product
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        f.add(p)
        result = algorithms.ir_filter(feed=f) # filter out out of stock product
        self.assertTrue(set(tiles) == set(result))

    def filter_placeholder_test(self):
        f = Feed.objects.get(pk=9) # has 2 in stock tiles
        tiles = list(f.tiles.all()) # force load
        p = Product.objects.get(pk=3) # in stock product
        p.placeholder = True
        p.save()
        f.add(p)
        result = algorithms.ir_filter(feed=f) # filter out out of stock product
        self.assertTrue(set(tiles) == set(result))

    def filter_out_of_stock_store_display_override_test(self):
        store = Store.objects.get(pk=1)
        store.display_out_of_stock = True # includes p in ir_filter
        store.save()

        f = Feed.objects.get(pk=9) # has 2 in stock tiles
        tiles = list(f.tiles.all()) # force load
        p = Product.objects.get(pk=12) # out of stock product
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        new_tile, _ = f.add(p)
        tiles.append(new_tile) # add out of stock tile

        result = algorithms.ir_filter(feed=f) # does not filter out of stock b/c store
        self.assertTrue(set(tiles) == set(result))

    def filter_no_feed_no_tiles_test(self):
        with self.assertRaises(ValueError): 
            algorithms.ir_filter()

class QSForTest(TestCase):
    fixtures = ['assets_models.json']

    def qs_for_test(self):
        tiles = [Tile.objects.get(pk=10)]
        result = qs_for(tiles)
        self.assertEqual(len(result), len(tiles))
        self.assertEqual(result.first().pk, tiles[0].pk)
        self.assertTrue(isinstance(result, QuerySet))

    def qs_for_all_test(self):
        feed = Feed.objects.get(pk=9)
        logging.debug(type(feed.tiles.all()))
        self.assertTrue(isinstance(feed.tiles.all(), QuerySet))
        result = qs_for(feed.tiles.all())
        self.assertEqual(len(result), len(feed.tiles.all()))
        self.assertEqual(result.first().pk, feed.tiles.all()[0].pk)
        self.assertTrue(isinstance(result, QuerySet))

    def qs_for_na_test(self):
        store = Store.objects.get(pk=1)
        # not iterable
        with self.assertRaises(TypeError):
            result = qs_for(store)

    def qs_for_none_test(self):
        result = qs_for(None)
        self.assertEqual(set(result), set(Tile.objects.none()))

