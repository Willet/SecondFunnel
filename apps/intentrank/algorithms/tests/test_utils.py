from django.test import TestCase
import mock
import logging
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned

from apps.utils.functional import may_be_json
from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
import apps.intentrank.serializers as ir_serializers
from apps.intentrank.serializers.utils import SerializerError
from apps.intentrank.algorithms.ir_magic import TemplateRatioEqualizer, TileRatioContainer
import apps.intentrank.algorithms as algorithms

class IRMagicTest(TestCase):
    fixtures = ['assets_models.json']

    def filter_tiles_test(self):
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        self.assertEqual(algorithms.ir_filter(tiles=tiles, feed=feed)[0], tiles[0])
        self.assertEqual(len(algorithms.ir_filter(tiles=tiles, feed=feed)), len(tiles))

    def filter_tiles_pi_tiles_test(self):
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        f = Feed.objects.get(pk=9)
        p = Product.objects.get(pk=3) # in stock product
        i = ProductImage.objects.get(pk=4)
        p.default_image = i
        p.product_images.add(i)
        f.add(p)
        logging.debug([t.placeholder for t in f.tiles.all()])
        # only tiles will be used b/c they are specifically specified
        rslt = algorithms.ir_filter(tiles=tiles, feed=feed)
        self.assertEqual(len(rslt), len(tiles))
        self.assertEqual(rslt[0], tiles.first())

    def filter_tiles_pi_test(self):
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        f = Feed.objects.get(pk=9)
        p = Product.objects.get(pk=3) # in stock product
        i = ProductImage.objects.get(pk=4)
        p.default_image = i
        p.product_images.add(i)
        f.add(p)
        logging.debug([t.placeholder for t in f.tiles.all()])
        rslt = algorithms.ir_filter(feed=feed)
        self.assertEqual(len(rslt), 2)
        self.assertEqual(len(feed.tiles.all()), 2)
        self.assertEqual(rslt[0], feed.tiles.first())
        self.assertEqual(rslt[1], feed.tiles.last())

    def filter_tiles_pi_oos_test(self):
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        f = Feed.objects.get(pk=9)
        p = Product.objects.get(pk=12) # out of stock product
        i = ProductImage.objects.get(pk=4)
        p.default_image = i
        p.product_images.add(i)
        f.add(p)
        self.assertEqual(algorithms.ir_filter(tiles=tiles, feed=feed)[0], tiles[0])
        self.assertEqual(len(algorithms.ir_filter(tiles=tiles, feed=feed)), len(tiles))

    def filter_tiles_pi_oos_display_anyway_test(self):
        store = Store.objects.get(pk=1)
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        f = Feed.objects.get(pk=9)
        p = Product.objects.get(pk=12) # out of stock product
        i = ProductImage.objects.get(pk=4)
        p.default_image = i
        p.product_images.add(i)
        f.add(p)
        store.display_out_of_stock = True # includes p in ir_filter
        store.save()
        logging.debug([t.placeholder for t in f.tiles.all()])
        raise Exception(algorithms.ir_filter(tiles=tiles, feed=feed))

    def filter_tiles_no_feed_no_tiles_test(self):
        with self.assertRaises(ValidationError): 
            algorithms.ir_filter()

class QSForTest(TestCase):
    fixtures = ['assets_models.json']

    def qs_for_test(self):
        tiles = [Tile.objects.get(pk=10)]
        result = algorithms.qs_for(tiles)
        self.assertEqual(len(result), len(tiles))
        self.assertEqual(result.first(), tiles[0])

