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

class IRPriorityTest(TestCase):
    fixtures = ['assets_models.json']

    def ir_priority_test(self):
        tiles = [Tile.objects.get(pk=10)]
        feed = Feed.objects.get(pk=9)
        self.assertEqual(algorithms.ir_priority(feed.tiles).first(), feed.tiles.first())

    def ir_priority_empty_test(self):
        feed = Feed.objects.get(pk=19)
        self.assertEqual(len(algorithms.ir_priority(feed.tiles)), len(feed.tiles.all()))