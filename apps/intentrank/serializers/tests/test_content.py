from django.test import TestCase
import mock
import logging

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               Gif, ProductImage, Feed, Tile, Content, Video
from apps.imageservice.models import ImageSizes
import apps.intentrank.serializers as ir_serializers
from apps.intentrank.serializers.utils import SerializerError, camelize_JSON

class ProductSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    s = ir_serializers.ProductSerializer()

    def get_dump_object_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        p.similar_products.add(p2)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11)
        p.product_images = [i, i2]
        p.attributes = {
            "foo": "bar",
            "hi_hi": "hello",
        }
        data = self.s.get_dump_object(p)
        # Check every key was correctly set in shallow dump
        # Other tests check specific key differences
        self.assertEqual(data["url"], p.url)
        self.assertEqual(data["sku"], p.sku)
        self.assertEqual(data["price"], p.price)
        self.assertEqual(data["salePrice"], p.sale_price)
        self.assertEqual(data["currency"], p.currency)
        self.assertEqual(data["description"], p.description)
        self.assertEqual(data["details"], p.details)
        self.assertEqual(data["name"], p.name)
        self.assertEqual(data["id"], p.id)
        self.assertEqual(data["in-stock"], p.in_stock)
        self.assertEqual(data["foo"], p.attributes["foo"])
        self.assertEqual(data["hiHi"], p.attributes["hi_hi"]) # converted to camelCase
        i_json = i.to_json()
        i2_json = i2.to_json()
        self.assertEqual(data['default-image'], i_json)
        # should be ordered 1st image (the default default) 1st
        self.assertEqual([i_json, i2_json], [data["images"][0], data["images"][1]])
        self.assertEqual(data["tagged-products"], [self.s.get_dump_object(p2, shallow=True)])

    def get_dump_object_default_image_test(self):
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11)
        p.product_images = [i, i2]
        p.default_image = i2
        p.save()
        data = self.s.get_dump_object(p)
        # default image should be 1st image
        i2_json = i2.to_json()
        self.assertEqual(data['default-image'], i2_json)
        # default image should be 1st
        self.assertEqual(data['images'][0], i2_json)

    def get_dump_object_no_image_test(self):
        p = Product.objects.get(pk=12)
        data = self.s.get_dump_object(p)
        self.assertEqual(data['default-image'], {})
        self.assertEqual(data["images"], [])

    def get_dump_object_ordered_images_test(self):
        p = Product.objects.get(pk=3)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=5)
        i3 = ProductImage.objects.get(pk=11)
        p.product_images = [i, i2, i3]
        p.attributes['product_images_order'] = [i3.id, i2.id, i.id]
        p.save()
        data = self.s.get_dump_object(p)
        self.assertEqual(data['images'][0], i3.to_json())
        self.assertEqual(data['images'][1], i2.to_json())
        self.assertEqual(data['images'][2], i.to_json())


    def get_dump_object_shallow_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        p.similar_products.add(p2)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11) # should be filtered out
        p.product_images = [i, i2]
        p.default_image = i2
        p.attributes = {
            "foo": "bar",
            "hi_hi": "hello",
        }
        data = self.s.get_dump_object(p, shallow=True)
        # Check every key was correctly set in shallow dump
        # Other tests check specific key differences
        self.assertEqual(data["url"], p.url)
        self.assertEqual(data["sku"], p.sku)
        self.assertEqual(data["price"], p.price)
        self.assertEqual(data["salePrice"], p.sale_price)
        self.assertEqual(data["currency"], p.currency)
        self.assertEqual(data["description"], p.description)
        self.assertEqual(data["details"], p.details)
        self.assertEqual(data["name"], p.name)
        self.assertEqual(data["id"], p.id)
        self.assertEqual(data["in-stock"], p.in_stock)
        self.assertEqual(data["foo"], p.attributes["foo"])
        self.assertEqual(data["hiHi"], p.attributes["hi_hi"]) # converted to camelCase
        # shallow product should have only default image
        i2_json = i2.to_json()
        self.assertEqual(data['default-image'], i2_json)
        self.assertEqual(data["images"], [i2_json])
        # shallow product should not have similar products
        self.assertEqual(data["tagged-products"], [])

    def get_dump_object_shallow_no_default_image_test(self):
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11) # should be filtered out
        p.product_images = [i, i2]
        data = self.s.get_dump_object(p, shallow=True)
        # shallow product should have only have 1st image b/c no default
        i_json = i.to_json()
        self.assertEqual(data['default-image'], i_json)
        self.assertEqual(data["images"], [i_json])

    def get_dump_object_shallow_no_image_test(self):
        p = Product.objects.get(pk=12)
        data = self.s.get_dump_object(p, shallow=True)
        self.assertEqual(data['default-image'], {})
        self.assertEqual(data["images"], [])

    def get_dump_object_similar_products_test(self):
        p = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3)
        p.similar_products = [p2, p3]
        data = self.s.get_dump_object(p)
        self.assertTrue(self.s.get_dump_object(p2, shallow=True) in data["tagged-products"])
        self.assertTrue(self.s.get_dump_object(p3, shallow=True) in data["tagged-products"])

    def get_dump_object_similar_products_placeholder_test(self):
        p = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3)
        p3.placeholder = True
        p3.in_stock = True
        p3.save()
        p.similar_products = [p3, p2]
        data = self.s.get_dump_object(p)
        self.assertEqual(data["tagged-products"], [self.s.get_dump_object(p2, shallow=True)])

    def get_dump_object_similar_products_out_of_stock_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=12) # out of stock
        p.similar_products = [p3, p2]
        data = self.s.get_dump_object(p)
        self.assertEqual(data["tagged-products"], [self.s.get_dump_object(p2, shallow=True)])

    def get_dump_object_similar_products_out_of_stock_store_override_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=12) # out of stock
        store = p.store
        store.display_out_of_stock = True
        store.save()
        p.similar_products = [p3, p2]
        data = self.s.get_dump_object(p)
        self.assertTrue(len(data["tagged-products"]) == 2)

    def get_dump_object_similar_products_shallow_test(self):
        p = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3) # should be filtered out
        p3.in_stock = True
        p3.save()
        p.similar_products.add(p2)
        p2.similar_products.add(p3)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11) # should be filtered out
        p2.product_images = [i, i2]
        p2.default_image = i
        p2.save()
        data = self.s.get_dump_object(p)
        # tagged-products should be shallow
        self.assertEqual(data["tagged-products"], [self.s.get_dump_object(p2, shallow=True)])
        tagged_product = data["tagged-products"][0]
        # shallow tagged-product should have no tagged-products
        self.assertEqual(tagged_product["tagged-products"], [])
        # shallow tagged-product should have be only default image
        i_json = i.to_json()
        self.assertEqual(tagged_product['default-image'], i_json)
        self.assertEqual(tagged_product['images'], [i_json])

    def get_dump_object_similar_products_first_image_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        p.similar_products.add(p2)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11) # should be filtered out
        p2.product_images = [i, i2]
        data = self.s.get_dump_object(p)
        tagged_product = data["tagged-products"][0]
        # shallow tagged-product image should be 1st image b/c no default_image
        i2_json = i2.to_json()
        self.assertEqual(tagged_product['default-image'], i2_json)
        self.assertEqual(tagged_product['images'], [i2_json])

    def get_dump_object_similar_products_no_image_test(self):
        p = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=3)
        p.similar_products.add(p2)
        data = self.s.get_dump_object(p)
        tagged_product = data["tagged-products"][0]
        # shallow tagged-product image should be empty
        self.assertEqual(tagged_product['default-image'], {})
        self.assertEqual(tagged_product['images'], [])


class ProductImageSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    s = ir_serializers.ProductImageSerializer()

    @mock.patch('apps.assets.models.ProductImage.is_product_shot', new_callable=mock.PropertyMock)
    def get_dump_object_test(self, mock_is_product_shot):
        mock_is_product_shot.return_value = True
        pi = ProductImage.objects.get(pk=4)
        pi.file_type = "png"
        pi.url = u"/image.png"
        pi.dominant_color = "FFF"
        pi.attributes = {"random_field": "random_value"}
        pi.image_sizes = ImageSizes(internal_dict={
            'h400': {
                'height': 400,
                'url': 'http://www.blah.com/image.jpg',
            },
            'master': {
                'width': 100,
                'height': 100,
                'url': 'http://www.blah.com/master.png',
            }
        })
        pi.save()
        data = self.s.get_dump_object(pi)
        self.assertEqual(data["format"], pi.file_type)
        self.assertEqual(data["type"], "image")
        self.assertEqual(data["dominant-color"], pi.dominant_color)
        self.assertEqual(data["url"], pi.url)
        self.assertEqual(data["id"], pi.id)
        self.assertEqual(data["orientation"], pi.orientation)
        self.assertEqual(data["sizes"], dict(pi.image_sizes))
        self.assertEqual(data["randomField"], pi.attributes["random_field"]) # camelCase
        mock_is_product_shot.assert_called_once_with()
        self.assertEqual(data["productShot"], True)

    def get_dump_object_defaults_test(self):
        pi = ProductImage.objects.get(pk=4)
        data = self.s.get_dump_object(pi)
        self.assertEqual(data["format"], "jpg") # default
        self.assertEqual(data["dominant-color"], "transparent") # default
        self.assertEqual(data["sizes"], {
            'master': {
                'url': pi.url, # default
                'width': '100%', # default
                'height': '100%', # default
            },
        })


class ContentSerializer(TestCase):
    fixtures = ['assets_models.json']

    s = ir_serializers.ContentSerializer()
    sp = ir_serializers.ProductSerializer()

    def get_dump_object_test(self):
        c = Content.objects.get(pk=6)
        c.source = "internet"
        c.source_url = "http://www.google.com"
        c.url = "http://www.blah.com/image.jpg"
        c.status = "approved"
        c.attributes = {
            "random_field": "random_value",
        }
        c.save()
        data = self.s.get_dump_object(c)
        self.assertEqual(data["id"], c.id)
        self.assertEqual(data["storeId"], c.store.id)
        self.assertEqual(data["source"], c.source)
        self.assertEqual(data["sourceUrl"], c.source_url)
        self.assertEqual(data["url"], c.url)
        self.assertEqual(data["status"], c.status)
        self.assertEqual(data["tagged-products"], [])
        self.assertEqual(data["randomField"], c.attributes["random_field"]) # camelCase

    def get_dump_object_tagged_products_test(self):
        c = Content.objects.get(pk=6)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3)
        c.tagged_products = [p2, p3]
        data = self.s.get_dump_object(c)
        self.assertTrue(self.sp.get_dump_object(p2, shallow=True) in data["tagged-products"])
        self.assertTrue(self.sp.get_dump_object(p3, shallow=True) in data["tagged-products"])

    def get_dump_object_tagged_products_placeholder_test(self):
        c = Content.objects.get(pk=6)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3)
        p3.placeholder = True
        p3.in_stock = True
        p3.save()
        c.tagged_products = [p3, p2]
        data = self.s.get_dump_object(c)
        self.assertEqual(data["tagged-products"], [self.sp.get_dump_object(p2, shallow=True)])

    def get_dump_object_tagged_products_out_of_stock_test(self):
        c = Content.objects.get(pk=6)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=12) # out of stock
        c.tagged_products = [p3, p2]
        data = self.s.get_dump_object(c)
        self.assertEqual(data["tagged-products"], [self.sp.get_dump_object(p2, shallow=True)])

    def get_dump_object_tagged_products_out_of_stock_store_override_test(self):
        c = Content.objects.get(pk=6)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=12) # out of stock
        store = c.store
        store.display_out_of_stock = True
        store.save()
        c.tagged_products = [p3, p2]
        data = self.s.get_dump_object(c)
        self.assertTrue(len(data["tagged-products"]) == 2)

    def get_dump_object_tagged_products_shallow_test(self):
        c = Content.objects.get(pk=6)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3) # should be filtered out
        p3.in_stock = True
        p3.save()
        c.tagged_products.add(p2)
        p2.similar_products.add(p3)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11) # should be filtered out
        p2.product_images = [i, i2]
        p2.default_image = i
        p2.save()
        data = self.s.get_dump_object(c)
        # tagged-products should be shallow
        self.assertEqual(data["tagged-products"], [self.sp.get_dump_object(p2, shallow=True)])
        tagged_product = data["tagged-products"][0]
        # shallow tagged-product should have no tagged-products
        self.assertEqual(tagged_product["tagged-products"], [])
        # shallow tagged-product should have be only default image
        i_json = i.to_json()
        self.assertEqual(tagged_product["default-image"], i_json)
        self.assertEqual(tagged_product["images"], [i_json])

    def get_dump_object_tagged_products_first_image_test(self):
        c = Content.objects.get(pk=6)
        p2 = Product.objects.get(pk=13)
        c.tagged_products.add(p2)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11) # should be filtered out
        p2.product_images = [i, i2]
        data = self.s.get_dump_object(c)
        tagged_product = data["tagged-products"][0]
        # shallow tagged-product image should be 1st image b/c no default_image
        i2_json = i2.to_json()
        self.assertEqual(tagged_product["default-image"], i2_json)
        self.assertEqual(tagged_product["images"], [i2_json])

    def get_dump_object_tagged_products_no_image_test(self):
        c = Content.objects.get(pk=6)
        p2 = Product.objects.get(pk=3)
        c.tagged_products.add(p2)
        data = self.s.get_dump_object(c)
        tagged_product = data["tagged-products"][0]
        # shallow tagged-product image should be empty
        self.assertEqual(tagged_product["default-image"], {})
        self.assertEqual(tagged_product["images"], [])


class ImageSerializer(TestCase):
    # Note: tagged_products are assumed to work, inherited from ContentSerializer
    fixtures = ['assets_models.json']

    s = ir_serializers.ImageSerializer()

    def get_dump_object_test(self):
        i = Image.objects.get(pk=6)
        i.source = "internet"
        i.soure_url = "www.google.com"
        i.url = u"/image.png"
        i.width = 100
        i.height = 100
        i.dominant_color = "FFF"
        i.status = "approved"
        i.attributes = {
            "sizes": {
                "h400": {
                    'height': 400,
                    'url': 'http://www.blah.com/image.jpg',
                },
                "master": {
                    'width': 100,
                    'height': 100,
                    'url': 'http://www.blah.com/master.png',
                },
            },
            "random_field": "random_value",
        }
        i.save()
        data = self.s.get_dump_object(i)
        self.assertEqual(data["id"], i.id)
        self.assertEqual(data["storeId"], i.store.id)
        self.assertEqual(data["source"], i.source)
        self.assertEqual(data["sourceUrl"], i.source_url)
        self.assertEqual(data["url"], i.url)
        self.assertEqual(data["status"], i.status)
        self.assertEqual(data["type"], "image")
        self.assertEqual(data["format"], "png")
        self.assertEqual(data["dominant-color"], i.dominant_color)
        self.assertEqual(data["orientation"], i.orientation, 'portrait')
        self.assertEqual(data["sizes"], i.attributes.get('sizes'))
        self.assertEqual(data["randomField"], i.attributes["random_field"]) # camelCase

    def get_dump_object_defaults_test(self):
        i = Image.objects.get(pk=6)
        data = self.s.get_dump_object(i)
        self.assertEqual(data["dominant-color"], "transparent") # default
        self.assertEqual(data["sizes"], {
            'master': {
                'url': i.url, # default
                'width': '100%', # default
                'height': '100%', # default
            },
        })


class GifSerializer(TestCase):
    # Note: tagged_products are assumed to work, inherited from ContentSerializer
    fixtures = ['assets_models.json']

    s = ir_serializers.GifSerializer()

    def get_dump_object_test(self):
        i = Gif.objects.get(pk=16)
        i.source = "internet"
        i.soure_url = "www.google.com"
        i.url = u"/image.png"
        i.gif_url = u"/image.gif"
        i.width = 100
        i.height = 100
        i.dominant_color = "FFF"
        i.status = "approved"
        i.attributes = {
            "sizes": {
                "h400": {
                    'height': 400,
                    'url': 'http://www.blah.com/image.jpg',
                },
                "master": {
                    'width': 100,
                    'height': 100,
                    'url': 'http://www.blah.com/master.png',
                },
            },
            "random_field": "random_value",
        }
        i.save()
        data = self.s.get_dump_object(i)
        self.assertEqual(data["id"], i.id)
        self.assertEqual(data["storeId"], i.store.id)
        self.assertEqual(data["source"], i.source)
        self.assertEqual(data["sourceUrl"], i.source_url)
        self.assertEqual(data["url"], i.url)
        self.assertEqual(data["status"], i.status)
        self.assertEqual(data["type"], "gif")
        self.assertEqual(data["format"], "png")
        self.assertEqual(data["dominant-color"], i.dominant_color)
        self.assertEqual(data["gifUrl"], i.gif_url)
        self.assertEqual(data["orientation"], i.orientation, 'portrait')
        self.assertEqual(data["sizes"], i.attributes.get('sizes'))
        self.assertEqual(data["randomField"], i.attributes["random_field"]) # camelCase

    def get_dump_object_defaults_test(self):
        i = Gif.objects.get(pk=16)
        data = self.s.get_dump_object(i)
        self.assertEqual(data["dominant-color"], "transparent") # default
        self.assertEqual(data["sizes"], {
            'master': {
                'url': i.url, # default
                'width': '100%', # default
                'height': '100%', # default
            },
        })


class VideoSerializer(TestCase):
    # Note: tagged_products are assumed to work, inherited from ContentSerializer
    fixtures = ['assets_models.json']

    s = ir_serializers.VideoSerializer()

    def get_dump_object_test(self):
        v = Video.objects.get(pk=6)
        v.source = "internet"
        v.soure_url = "www.google.com"
        v.url = u"www.youtube.com/watch?v=KfKFqidUe4M"
        v.name = "hello world"
        v.description = "a simple hello, to the world"
        v.status = "approved"
        v.original_id = "KfKFqidUe4M"
        v.attributes = {
            "random_field": "random_value",
        }
        v.save()
        data = self.s.get_dump_object(v)
        self.assertEqual(data["id"], v.id)
        self.assertEqual(data["storeId"], v.store.id)
        self.assertEqual(data["source"], v.source)
        self.assertEqual(data["sourceUrl"], v.source_url)
        self.assertEqual(data["url"], v.url)
        self.assertEqual(data["status"], v.status)
        self.assertEqual(data["name"], v.name)
        self.assertEqual(data["description"], v.description)
        self.assertEqual(data["type"], "video")
        self.assertEqual(data["original-id"], v.original_id)
        self.assertEqual(data["randomField"], v.attributes["random_field"]) # camelCase

    def get_dump_object_defaults_test(self):
        v = Video.objects.get(pk=6)
        data = self.s.get_dump_object(v)
        self.assertEqual(data["name"], "") # default
        self.assertEqual(data["description"], "") # default
        self.assertEqual(data["original-id"], v.id) # default
