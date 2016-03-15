from django.test import TestCase
import mock

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Video, Feed, Tile, Content
from apps.intentrank.serializers.tiles import TileSerializer, DefaultTileSerializer, \
        ProductTileSerializer, ImageTileSerializer, GifTileSerializer, VideoTileSerializer, \
        BannerTileSerializer, CollectionTileSerializer, HeroTileSerializer, HerovideoTileSerializer
from apps.intentrank.serializers.utils import SerializerError


class TileSerializerTest(TestCase):
    fixtures = ['assets_intentrank.json']
    s = TileSerializer()

    def call_test(self):
        self.assertEqual(self.s.__call__("default"), DefaultTileSerializer)
        self.assertEqual(self.s.__call__("Product"), ProductTileSerializer)
        self.assertEqual(self.s.__call__("Image"), ImageTileSerializer)
        self.assertEqual(self.s.__call__("Gif"), GifTileSerializer)
        self.assertEqual(self.s.__call__("Video"), VideoTileSerializer)
        self.assertEqual(self.s.__call__("Banner"), BannerTileSerializer)
        self.assertEqual(self.s.__call__("Collection"), CollectionTileSerializer)
        self.assertEqual(self.s.__call__("Hero"), HeroTileSerializer)
        self.assertEqual(self.s.__call__("Herovideo"), HerovideoTileSerializer)
        self.assertEqual(self.s.__call__("random_string"), DefaultTileSerializer)

    def get_core_attributes_test(self):
        t = Tile.objects.get(pk=10)
        data = self.s.get_core_attributes(t)
        self.assertEqual(data['template'], 'default')
        self.assertEqual(data['priority'], 0)
        self.assertEqual(data['tile-id'], 10)

    def get_dump_object_test(self):
        with self.assertRaises(NotImplementedError):
            self.s.get_dump_object(None)

    def get_dump_separated_content_test(self):
        t = Tile.objects.get(pk=10)
        self.assertEqual(self.s.get_dump_separated_content(t), {})
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = self.s.get_dump_separated_content(t)
        self.assertEqual(data['default-image'], i.to_json())

    def get_dump_first_content_of_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        v = Video.objects.get(pk=18)
        t.content = [i, v]
        data = self.s.get_dump_first_content_of('assets.Image', t)
        self.assertEqual(data, i.to_json())
        data = self.s.get_dump_first_content_of('assets.Video', t)
        self.assertEqual(data, v.to_json())
        with self.assertRaises(LookupError):
            self.s.get_dump_first_content_of('assets.Review', t)

    def get_dump_tagged_products_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=12) # out of stock
        t.products.add(p)

        products = self.s.get_dump_tagged_products(t)
        self.assertEqual(products, [p.to_json()])
        # Should hide out of stock
        t.products.remove(p)
        t.products.add(p2)
        products = self.s.get_dump_tagged_products(t)
        self.assertEqual(products, [])
        # Store override, display out of stock
        s = t.feed.store
        s.display_out_of_stock = True
        s.save()
        products = self.s.get_dump_tagged_products(t)
        self.assertEqual(products, [p2.to_json()])


class DefaultTileSerializerTest(TestCase):
    fixtures = ['assets_intentrank.json']
    s =  DefaultTileSerializer()

    def get_dump_object_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=3)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [])

        t.products.add(p)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])

    def get_dump_object_out_of_stock_product_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12) # out of stock
        t.products.add(p)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [])

        s = t.feed.store
        s.display_out_of_stock = True
        s.save()

        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])


class ProductTileSerializerTest(TestCase):
    fixtures = ['assets_intentrank.json']
    s =  ProductTileSerializer()

    def get_dump_object_test(self):
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no products
            data = self.s.get_dump_object(t)

        p = Product.objects.get(pk=3)
        t.products.add(p)
        with self.assertRaises(SerializerError):
            # no defaut image
            data = self.s.get_dump_object(t)

        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['product'], p.to_json())


class ImageTileSerializerTest(TestCase):
    # All of these tests apply to GifTileSerializer too
    fixtures = ['assets_intentrank.json']
    s =  ImageTileSerializer()

    def get_dump_object_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())

    def get_dump_object_no_image_test(self):
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            data = self.s.get_dump_object(t)

    def get_dump_object_default_image_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        i2 = Image.objects.get(pk=8)
        t.content = [i, i2]
        t.attributes['default-image'] = i2.id # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['default-image'], i2.to_json())

        del t.attributes['default-image']
        t.attributes['defaultImage'] = i.id # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())

        t.attributes['defaultImage'] = 135246234
        with self.assertRaises(SerializerError):
            # Default image doesn't exist in content
            data = self.s.get_dump_object(t)

    def get_dump_object_expandedImage_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        i2 = Image.objects.get(pk=8)
        t.content = [i, i2]
        t.attributes['default-image'] = i.id
        data = self.s.get_dump_object(t)
        self.assertFalse('expandedImage' in data)

        t.attributes['expanded-image'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['expandedImage'], i2.to_json())

        del t.attributes['expanded-image']
        t.attributes['expandedImage'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['expandedImage'], i2.to_json())
        
        t.attributes['expandedImage'] = 135246234
        with self.assertRaises(SerializerError):
            # Expanded image doesn't exist in content
            data = self.s.get_dump_object(t)

    def get_dump_object_mobileExpandedImage_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        i2 = Image.objects.get(pk=8)
        t.content = [i, i2]
        t.attributes['default-image'] = i.id
        data = self.s.get_dump_object(t)
        self.assertFalse('mobileExpandedImage' in data)

        t.attributes['mobile-expanded-image'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['mobileExpandedImage'], i2.to_json())

        del t.attributes['mobile-expanded-image']
        t.attributes['mobileExpandedImage'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['mobileExpandedImage'], i2.to_json())
        
        t.attributes['mobileExpandedImage'] = 135246234
        with self.assertRaises(SerializerError):
            # Expanded image doesn't exist in content
            data = self.s.get_dump_object(t)

    def get_dump_object_tagged_product_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=3)
        pi = ProductImage.objects.get(pk=4)
        i = Image.objects.get(pk=6)
        p.product_images.add(pi)
        t.products.add(p)
        t.content.add(i)

        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'],[p.to_json()])

        t.products.remove(p)
        i.tagged_products.add(p)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'],[p.to_json()])

    def get_dump_object_out_of_stock_product_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12)
        pi = ProductImage.objects.get(pk=4)
        i = Image.objects.get(pk=6)
        p.product_images.add(pi)
        t.products.add(p)
        t.content.add(i)

        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [])

        s = t.feed.store
        s.display_out_of_stock = True
        s.save()
        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])


class VideoTileSerializerTest(TestCase):
    fixtures = ['assets_intentrank.json']
    s =  VideoTileSerializer()

    def get_dump_object_video_test(self):
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no video
            data = self.s.get_dump_object(t)

        v = Video.objects.get(pk=18)
        t.content.add(v)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['video'], v.to_json())
        self.assertEqual(data['tagged-products'], [])

    def get_dump_object_tagged_products_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=3)
        i = ProductImage.objects.get(pk=4)
        v = Video.objects.get(pk=18)
        p.product_images.add(i)
        t.products.add(p)
        t.content.add(v)
        # Tile tagged with product
        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])
        # Video tagged with product
        t.products.remove(p)
        v.tagged_products.add(p)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])

    def get_dump_object_out_of_stock_product_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12) # out of stock
        i = ProductImage.objects.get(pk=4)
        v = Video.objects.get(pk=18)
        p.product_images.add(i)
        t.products.add(p)
        t.content.add(v)

        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [])

        s = t.feed.store
        s.display_out_of_stock = True
        s.save()

        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])


class BannerTileSerializerTest(TestCase):
    fixtures = ['assets_intentrank.json']
    s =  BannerTileSerializer()

    def get_dump_object_image_test(self):
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no image, no product image
            data = self.s.get_dump_object(t)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())

    def get_dump_object_product_image_test(self):
        # Banner tile tries to use a product image if there is not images
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no product
            data = self.s.get_dump_object(t)
        p = Product.objects.get(pk=3)
        t.products.add(p)
        with self.assertRaises(SerializerError):
            # no product image
            data = self.s.get_dump_object(t)
        i = ProductImage.objects.get(pk=4)
        p.product_images.add(i)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())

    def get_dump_object_redirect_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = self.s.get_dump_object(t)
        self.assertTrue('redirectUrl' not in data)
        t.attributes['redirect_url'] = 'http://www.facebook.com'
        data = self.s.get_dump_object(t)
        self.assertEqual(data['redirectUrl'], t.attributes['redirect_url'])
        del t.attributes['redirect_url']
        t.attributes['redirect-url'] = 'http://www.google.com'
        data = self.s.get_dump_object(t)
        self.assertEqual(data['redirectUrl'], t.attributes['redirect-url'])


class CollectionTileSerializerTest(TestCase):
    fixtures = ['assets_intentrank.json']
    s = CollectionTileSerializer()

    def get_dump_object_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=3)
        i = Image.objects.get(pk=6)
        with self.assertRaises(SerializerError):
            # no image
            data = self.s.get_dump_object(t)
        t.content.add(i)
        t.products.add(p)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())
        self.assertEqual(data['tagged-products'], [p.to_json()])

    def get_dump_object_default_image_missing_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        i2 = Image.objects.get(pk=8)
        t.content = [i, i2]
        t.attributes['defaultImage'] = 999
        with self.assertRaises(SerializerError):
            # default image doesn't exist
            self.s.get_dump_object(t)
        del t.attributes['defaultImage']
        t.attributes['default-image'] = 999
        with self.assertRaises(SerializerError):
            # default image doesn't exist
            self.s.get_dump_object(t)
        del t.attributes['default-image']
        t.attributes['default_image'] = 999
        with self.assertRaises(SerializerError):
            # default image doesn't exist
            self.s.get_dump_object(t)

    def get_dump_object_expandedImage_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        i2 = Image.objects.get(pk=8)
        t.content = [i, i2]
        t.attributes['default-image'] = i.id
        data = self.s.get_dump_object(t)
        self.assertFalse('expandedImage' in data)

        t.attributes['expanded-image'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['expandedImage'], i2.to_json())

        del t.attributes['expanded-image']
        t.attributes['expandedImage'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['expandedImage'], i2.to_json())
        
        t.attributes['expandedImage'] = 135246234
        with self.assertRaises(SerializerError):
            # Expanded image doesn't exist in content
            data = self.s.get_dump_object(t)

    def get_dump_object_mobileExpandedImage_test(self):
        t = Tile.objects.get(pk=10)
        i = Image.objects.get(pk=6)
        i2 = Image.objects.get(pk=8)
        t.content = [i, i2]
        t.attributes['default-image'] = i.id
        data = self.s.get_dump_object(t)
        self.assertFalse('mobileExpandedImage' in data)

        t.attributes['mobile-expanded-image'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['mobileExpandedImage'], i2.to_json())

        del t.attributes['mobile-expanded-image']
        t.attributes['mobileExpandedImage'] = i2.id  # testing this key
        data = self.s.get_dump_object(t)
        self.assertEqual(data['mobileExpandedImage'], i2.to_json())
        
        t.attributes['mobileExpandedImage'] = 135246234
        with self.assertRaises(SerializerError):
            # Expanded image doesn't exist in content
            data = self.s.get_dump_object(t)

    def get_dump_object_out_of_stock_product_test(self):
        t = Tile.objects.get(pk=10)
        p = Product.objects.get(pk=12) # out of stock
        pi = ProductImage.objects.get(pk=4)
        i = Image.objects.get(pk=6)
        v = Video.objects.get(pk=18)
        p.product_images.add(pi)
        t.products.add(p)
        t.content = [i, v]

        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [])

        s = t.feed.store
        s.display_out_of_stock = True
        s.save()

        data = self.s.get_dump_object(t)
        self.assertEqual(data['tagged-products'], [p.to_json()])


class HeroTileSerializerTest(TestCase):
    fixtures = ['assets_intentrank.json']
    s =  HeroTileSerializer()

    def get_dump_object_test(self):
        t = Tile.objects.get(pk=10)
        with self.assertRaises(SerializerError):
            # no image
            data = self.s.get_dump_object(t)
        i = Image.objects.get(pk=6)
        t.content.add(i)
        data = self.s.get_dump_object(t)
        self.assertEqual(data['default-image'], i.to_json())
