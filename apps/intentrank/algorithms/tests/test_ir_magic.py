from django.test import TestCase
import mock
import logging
from datetime import datetime
from django.conf import settings

from apps.utils.functional import may_be_json
from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
import apps.intentrank.serializers as ir_serializers
from apps.intentrank.serializers.utils import SerializerError
from apps.intentrank.algorithms.ir_magic import TemplateRatioEqualizer, TileRatioContainer
import apps.intentrank.algorithms as algorithms


class IRMagicTest(TestCase):
    fixtures = ['assets_models.json']

    def ir_magic_test(self):
        feed = Feed.objects.get(pk=9)
        product = Product.objects.get(pk=3)
        pi = ProductImage.objects.get(pk=4)
        product.default_image = pi
        product.product_images.add(pi)
        feed.add(product)
        self.assertEqual(algorithms.ir_magic(feed.tiles).first(), feed.tiles.first())

    def ir_magic_duplicate_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=9)
        feed.tiles.add(tile)
        self.assertEqual(len(algorithms.ir_magic(feed.tiles)), len(feed.tiles.all()))

    def ir_magic_none_test(self):
        feed = Feed.objects.get(pk=19)
        self.assertEqual(len(algorithms.ir_magic(feed.tiles)), len(feed.tiles.all()))

class TemplateRatioEqualizerTest(TestCase):
    fixtures = ['assets_models.json']

    def init_test(self):
        feed = Feed.objects.get(pk=19)
        tre = TemplateRatioEqualizer(feed.tiles)
        self.assertEqual(tre.candidates, [])
        self.assertEqual(tre.highest_priority, None)

    def next_test(self):
        feed = Feed.objects.get(pk=19)
        product = Product.objects.get(pk=15)
        pi = ProductImage.objects.get(pk=4)
        product.default_image = pi
        product.product_images.add(pi)
        newTile, success = feed.add(product)
        newTile2 = Tile.objects.create(feed=feed, template="default")
        tre = TemplateRatioEqualizer(feed.tiles)
        self.assertEqual(tre.next(), newTile2)
        self.assertEqual(tre.next(), newTile)

    def tre_get_next_highest_priority_tiles_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=19)
        new_tile = Tile.objects.create(feed=feed, template="default")
        tre = TemplateRatioEqualizer(feed.tiles)
        self.assertEqual(tre.candidates, [])
        tre._get_next_highest_priority_tiles()
        self.assertEqual(tre.candidates, [{'tile': new_tile, 'ratio': 0.0}])

    def tre_replace_tile_of_template_test(self):
        feed = Feed.objects.get(pk=19)
        new_tile = Tile.objects.create(feed=feed, template="default")
        tre = TemplateRatioEqualizer(feed.tiles)
        tre._get_next_highest_priority_tiles()
        self.assertIsNone(tre._replace_tile_of_template(u"default"))
        # tre._replace_tile_of_template("tile")

class TileRatioContainerTest(TestCase):
    fixtures = ['assets_models.json']

    def init_empty_test(self):
        feed = Feed.objects.get(pk=19)
        trc = TileRatioContainer(feed.tiles.all(), len(feed.tiles.all()))
        self.assertEqual(len(trc.tiles), len(feed.tiles.all()))
        self.assertEqual(trc.total, len(feed.tiles.all()))
        self.assertEqual(trc.ratio, 0)
        self.assertEqual(trc.num_total_tiles, 0)
        self.assertEqual(trc.num_added, 0)

    def init_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=9)
        feed.add(tile)
        trc = TileRatioContainer(feed.tiles.all(), len(feed.tiles.all()))
        self.assertTrue(set(trc.tiles) == set(feed.tiles.all()))
        self.assertEqual(trc.total, feed.tiles.count())
        self.assertEqual(trc.ratio, 1)
        self.assertEqual(trc.num_total_tiles, feed.tiles.count())
        self.assertEqual(trc.num_added, 0)

    def get_next_tile_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=9)
        new_tile = Tile.objects.create(feed=feed, template="default")
        logging.debug(feed.tiles.all())
        trc = TileRatioContainer(feed.tiles.all(), len(feed.tiles.all()))
        self.assertEqual(trc.num_added, 0)
        nt1 = trc.get_next_tile()
        nt2 = trc.get_next_tile()
        logging.debug(nt1)
        logging.debug(nt2)
        self.assertEqual(nt1, {'tile': feed.tiles.all()[0], 'ratio': 0.0})
        self.assertEqual(nt2, {'tile': feed.tiles.all()[0], 'ratio': 0.0})

    def get_next_tile_empty_test(self):
        feed = Feed.objects.get(pk=19)
        trc = TileRatioContainer(feed.tiles.all(), len(feed.tiles.all()))
        self.assertEqual(trc.get_next_tile(), None)
