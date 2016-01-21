from django.test import TestCase
import mock
import logging

from apps.assets.models import BaseModel, Store, Theme, Tag, Category, Page, Product, Image, \
                               ProductImage, Feed, Tile, Content
import apps.intentrank.serializers as ir_serializers
from apps.intentrank.serializers.utils import SerializerError, camelize_JSON

class ProductSerializerTest(TestCase):
    fixtures = ['assets_models.json']

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
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
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
        self.assertEqual(data["tagged-products"], [s.get_dump_object(p2, shallow=True)])

    def get_dump_object_default_image_test(self):
        p = Product.objects.get(pk=12)
        i = ProductImage.objects.get(pk=4)
        i2 = ProductImage.objects.get(pk=11)
        p.product_images = [i, i2]
        p.default_image = i2
        p.save()
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        # default image should be 1st image
        i2_json = i2.to_json()
        self.assertEqual(data['default-image'], i2_json)
        # default image should be 1st
        self.assertEqual(data['images'][0], i2_json)

    def get_dump_object_no_image_test(self):
        p = Product.objects.get(pk=12)
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
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
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
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
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p, shallow=True)
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
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p, shallow=True)
        # shallow product should have only have 1st image b/c no default
        i_json = i.to_json()
        self.assertEqual(data['default-image'], i_json)
        self.assertEqual(data["images"], [i_json])

    def get_dump_object_shallow_no_image_test(self):
        p = Product.objects.get(pk=12)
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p, shallow=True)
        self.assertEqual(data['default-image'], {})
        self.assertEqual(data["images"], [])

    def get_dump_object_similar_products_test(self):
        p = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3)
        p.similar_products = [p2, p3]
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        self.assertTrue(s.get_dump_object(p2, shallow=True) in data['tagged-products'])
        self.assertTrue(s.get_dump_object(p3, shallow=True) in data['tagged-products'])

    def get_dump_object_similar_products_placeholder_test(self):
        p = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=3)
        p3.placeholder = True
        p3.in_stock = True
        p3.save()
        p.similar_products = [p3, p2]
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        self.assertEqual(data['tagged-products'], [s.get_dump_object(p2, shallow=True)])

    def get_dump_object_similar_products_out_of_stock_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=12) # out of stock
        p.similar_products = [p3, p2]
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        self.assertEqual(data['tagged-products'], [s.get_dump_object(p2, shallow=True)])

    def get_dump_object_similar_products_out_of_stock_store_override_test(self):
        p = Product.objects.get(pk=3)
        p2 = Product.objects.get(pk=13)
        p3 = Product.objects.get(pk=12) # out of stock
        store = p.store
        store.display_out_of_stock = True
        store.save()
        p.similar_products = [p3, p2]
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        self.assertTrue(len(data['tagged-products']) == 2)

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
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        # tagged-products should be shallow
        self.assertEqual(data['tagged-products'], [s.get_dump_object(p2, shallow=True)])
        tagged_product = data['tagged-products'][0]
        # shallow tagged-product should have no tagged-products
        self.assertEqual(tagged_product['tagged-products'], [])
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
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        tagged_product = data['tagged-products'][0]
        # shallow tagged-product image should be 1st image b/c no default_image
        i2_json = i2.to_json()
        self.assertEqual(tagged_product['default-image'], i2_json)
        self.assertEqual(tagged_product['images'], [i2_json])

    def get_dump_object_similar_products_no_image_test(self):
        p = Product.objects.get(pk=12)
        p2 = Product.objects.get(pk=3)
        p.similar_products.add(p2)
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(p)
        tagged_product = data['tagged-products'][0]
        # shallow tagged-product image should be empty
        self.assertEqual(tagged_product['default-image'], {})
        self.assertEqual(tagged_product['images'], [])


class ProductImageSerializerTest(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s = ir_serializers.ProductImageSerializer()
        product_image = ProductImage.objects.get(pk=4)
        attributes = {"random_field": "random_value"}
        product_image.attributes = attributes
        data = product_image.serializer().get_dump_object(product_image)
        self.assertEqual(data["format"], product_image.file_type or "jpg")
        self.assertEqual(data["type"], "image")
        self.assertEqual(data["dominant-color"], "transparent")
        self.assertEqual(data["url"], product_image.url)
        self.assertEqual(data["id"], product_image.id)
        self.assertEqual(data["orientation"], product_image.orientation)
        self.assertEqual(data["sizes"], {
            'master': {
                'url': u'/image.jpg',
                'width': '100%',
                'height': '100%',
            },
        })

        logging.debug(data)

        self.assertEqual(data["randomField"], "random_value")
        #how to test product shot???


class ContentSerializer(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s = ir_serializers.ContentSerializer()
        content = Content.objects.get(pk=6)
        data = s.get_dump_object(content)
        self.assertEqual(data['id'], content.id)
        self.assertEqual(data['store-id'], str(content.store.id if content.store else 0))
        self.assertEqual(data['source'], content.source)
        self.assertEqual(data['source_url'], content.source_url)
        self.assertEqual(data['url'], content.url or content.source_url)
        self.assertEqual(data['author'], content.author)
        self.assertEqual(data['status'], content.status)
        self.assertEqual(data['tagged-products'], [])


class ImageSerializer(TestCase):
    fixtures = ['assets_models.json']

    def get_dump_object_test(self):
        s = ir_serializers.ImageSerializer()
        image = Image.objects.get(pk=6)
        data = s.get_dump_object(image)
        self.assertEqual(data["type"], "image")
        self.assertEqual(data["dominant-color"], getattr(image, "dominant_color", "transparent"))
        self.assertEqual(data["status"], image.status)
        self.assertEqual(data["orientation"], getattr(image, 'orientation', 'portrait'))
        self.assertEqual(data["sizes"], image.attributes.get('sizes', {
                    'width': getattr(image, "width", '100%'),
                    'height': getattr(image, "height", '100%'),
                }))
