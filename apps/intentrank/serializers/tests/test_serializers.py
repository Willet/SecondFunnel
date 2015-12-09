from django.test import TestCase
import mock
import logging

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
from apps.intentrank.serializers.tiles import TileSerializer, DefaultTileSerializer, \
  ProductTileSerializer, ImageTileSerializer, GifTileSerializer, VideoTileSerializer, \
  BannerTileSerializer, CollectionTileSerializer, HeroTileSerializer, HerovideoTileSerializer

class TileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_core_attributes_test(self):
        t = Tile.objects.get(pk=10)
        s = TileSerializer()
        data = s.get_core_attributes(t)
        self.assertEqual(data['template'], 'default')
        self.assertEqual(data['priority'], 0)
        self.assertEqual(data['tile-id'], 10)

    def get_dump_object_test(self):
        s = TileSerializer()
        with self.assertRaises(NotImplementedError):
            s.get_dump_object(None)

    def get_dump_separated_content_test(self):
        s =  TileSerializer()
        t = Tile.objects.get(pk=10)
        self.assertEqual(s.get_dump_separated_content(t), {})
        # i = Content.objects.get(pk=6)
        # t.content.add(i)
        # data = s.get_dump_separated_content(t)
        # logging.debug(data['default-image'])
        # logging.debug(i.to_json())
        # # these aren't equal and I don't know why
        # self.assertEqual(data['default-image'], i.to_json())

    
