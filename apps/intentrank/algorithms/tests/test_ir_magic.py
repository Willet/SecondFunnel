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
from apps.intentrank.algorithms.ir_magic import TemplateRatioEqualizer
import apps.intentrank.algorithms as algorithms


class IRMagicTest(TestCase):
    fixtures = ['assets_models.json']

    def ir_magic_test(self):
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        self.assertEqual(algorithms.ir_magic(feed.tiles), [feed.tiles.first()])
        

    def ir_magic_duplicate_test(self):
        tile = Tile.objects.get(pk=10)
        feed = Feed.objects.get(pk=9)
        feed.tiles.add(tile)
        self.assertEqual(algorithms.ir_magic(feed.tiles), [feed.tiles.first()])

    def ir_magic_none_test(self):
        feed = Feed.objects.get(pk=19)
        self.assertEqual(algorithms.ir_magic(feed.tiles), [])

class TemplateRatioEqualizerTest(TestCase):
    fixtures = ['assets_models.json']

    def init_test(self):
        feed = Feed.objects.get(pk=19)
        tre = TemplateRatioEqualizer(feed.tiles)
        self.assertEqual(tre.candidates, [])
        self.assertEqual(tre.highest_priority, None)

    def next_test(self):
        feed = Feed.objects.get(pk=19)
        newTile = Tile.objects.create(feed=feed, template="default")
        newTile2 = Tile.objects.create(feed=feed, template="default")
        tre = TemplateRatioEqualizer(feed.tiles)
        self.assertEqual(tre.next(), newTile)
        self.assertEqual(tre.next(), newTile2)
