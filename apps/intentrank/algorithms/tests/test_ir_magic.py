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
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        self.assertEqual(algorithms.ir_magic(feed.tiles).first(), feed.tiles.first())
        

    def ir_magic_duplicate_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=9)
        feed.tiles.add(tile)
        self.assertEqual(algorithms.ir_magic(feed.tiles), [feed.tiles.first()])

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
        newTile = feed.add(product) #broken
        newTile2 = Tile.objects.create(feed=feed, template="default")
        tre = TemplateRatioEqualizer(feed.tiles)
        self.assertEqual(tre.next(), newTile)
        self.assertEqual(tre.next(), newTile2)

    def tre_get_next_highest_priority_tiles_test(self):
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
        self.assertEqual(trc.tiles, feed.tiles.all())
        self.assertEqual(trc.total, len(feed.tiles.all()))
        self.assertEqual(trc.ratio, 0)
        self.assertEqual(trc.num_total_tiles, 0)
        self.assertEqual(trc.num_added, 0)

    def init_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=9)
        feed.tiles.add(tile)
        trc = TileRatioContainer(feed.tiles.all(), len(feed.tiles.all()))
        self.assertEqual(trc.tiles, feed.tiles.all())
        self.assertEqual(trc.total, len(feed.tiles.all()))
        self.assertEqual(trc.ratio, 0)
        self.assertEqual(trc.num_total_tiles, 0)
        self.assertEqual(trc.num_added, 0)

    def get_next_tile_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=9)
        new_tile = Tile.objects.create(feed=feed, template="default")
        feed.add(new_tile)
        trc = TileRatioContainer(feed.tiles.all(), len(feed.tiles.all()))
        self.assertEqual(trc.num_added, 0)
        self.assertEqual(trc.get_next_tile(), {'tile': new_tile, 'ratio': 0.0})

    def get_next_tile_empty_test(self):
        feed = Feed.objects.get(pk=19)
        trc = TileRatioContainer(feed.tiles.all(), len(feed.tiles.all()))
        self.assertEqual(trc.get_next_tile(), None)
