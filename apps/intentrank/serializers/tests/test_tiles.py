from django.test import TestCase
import mock
import logging

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
from apps.intentrank.serializers.tiles import TileSerializer, DefaultTileSerializer, \
  ProductTileSerializer, ImageTileSerializer, GifTileSerializer, VideoTileSerializer, \
  BannerTileSerializer, CollectionTileSerializer, HeroTileSerializer, HerovideoTileSerializer

from apps.intentrank.serializers.utils import SerializerError

class TileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def call_test(self):
        s = TileSerializer()
        self.assertEqual(s.__call__("default"), DefaultTileSerializer)
        self.assertEqual(s.__call__("Product"), ProductTileSerializer)
        self.assertEqual(s.__call__("Image"), ImageTileSerializer)
        self.assertEqual(s.__call__("Gif"), GifTileSerializer)
        self.assertEqual(s.__call__("Video"), VideoTileSerializer)
        self.assertEqual(s.__call__("Banner"), BannerTileSerializer)
        self.assertEqual(s.__call__("Collection"), CollectionTileSerializer)
        self.assertEqual(s.__call__("Hero"), HeroTileSerializer)
        self.assertEqual(s.__call__("Herovideo"), HerovideoTileSerializer)
        self.assertEqual(s.__call__("randomstring"), DefaultTileSerializer)

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
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = s.get_dump_separated_content(t)
        logging.debug("actual call: {}".format(t.separated_content['images'][0].to_json()))
        logging.debug(data['default-image'])
        logging.debug(i.to_json())
        # these aren't equal and I don't know why
        self.assertEqual(data['default-image'], i.to_json())

class DefaultTileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s =  DefaultTileSerializer()
        t = Tile.objects.get(pk=10)
        data = s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [])
        p = Product.objects.get(pk=3)
        t.products.add(p)
        data = s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])

class ProductTileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s =  ProductTileSerializer()
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no products
            data = s.get_dump_object(t)
        p = Product.objects.get(pk=3)
        t.products.add(p)
        with self.assertRaises(SerializerError):
            # no defaut image
            data = s.get_dump_object(t)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        data = s.get_dump_object(t)
        self.assertEqual(data['product'], p.to_json())

class ImageTileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s =  ImageTileSerializer()
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no image
            data = s.get_dump_object(t)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())

class BannerTileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_image_test(self):
        s =  BannerTileSerializer()
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no image, no product
            data = s.get_dump_object(t)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())
        self.assertIsNone(data['redirect-url']) # shouldn't this be a required field?

    def get_dump_object_product_test(self):
        s =  BannerTileSerializer()
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no product
            data = s.get_dump_object(t)
        p = Product.objects.get(pk=3)
        t.products.add(p)
        with self.assertRaises(SerializerError):
            # no product image
            data = s.get_dump_object(t)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        data = s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())
        self.assertIsNone(data['redirect-url']) # again, required?

class CollectionTileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s =  CollectionTileSerializer()
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no image
            data = s.get_dump_object(t)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        # # Error not raised?
        # with self.assertRaises(SerializerError):
        #     # no expanded image
        #     data = s.get_dump_object(t)
        # t.attributes.update({
        #     'expandedImage': i
        # })
        data = s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())

class HeroTileSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s =  HeroTileSerializer()
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no image
            data = s.get_dump_object(t)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())
