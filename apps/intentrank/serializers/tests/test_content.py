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
        product = Product.objects.get(pk=3)
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(product)
        self.assertEqual(data['default-image'], {})
        self.assertEqual(data['sizes'], {})
        self.assertEqual(data['orientation'], "portrait")
        self.assertEqual(data["url"], product.url)
        self.assertEqual(data["sku"], getattr(product, "sku", ""))
        self.assertEqual(data["price"], product.price)
        self.assertEqual(data["salePrice"], product.sale_price)
        self.assertEqual(data["currency"], product.currency)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(data["details"], product.details)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["tagged-products"], [])
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["in-stock"], product.in_stock)
        self.assertEqual(data["images"], [])

    def get_dump_object_shallow_test(self):
        product = Product.objects.get(pk=12)
        image = ProductImage.objects.get(pk=4)
        product.product_images.add(image)
        s = ir_serializers.ProductSerializer()
        data = s.get_dump_object(product, shallow=True)
        self.assertEqual(data['default-image'], image.to_json())
        self.assertEqual(data['sizes'], None)
        self.assertEqual(data['orientation'], "portrait")
        self.assertEqual(data["url"], product.url)
        self.assertEqual(data["sku"], getattr(product, "sku", ""))
        self.assertEqual(data["price"], product.price)
        self.assertEqual(data["salePrice"], product.sale_price)
        self.assertEqual(data["currency"], product.currency)
        self.assertEqual(data["description"], product.description)
        self.assertEqual(data["details"], product.details)
        self.assertEqual(data["name"], product.name)
        self.assertEqual(data["tagged-products"], [])
        self.assertEqual(data["id"], product.id)
        self.assertEqual(data["in-stock"], product.in_stock)
        self.assertEqual(data["images"], [{
            'orientation': 'portrait',
            'sizes': {
                'width': 0,
                'height': 0
            },
            'url': u'/image.jpg',
            'format': 'jpg',
            'productShot': False,
            'dominant-color': 'transparent',
            'type': 'image',
            'id': 4,
        }])

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
        self.assertEqual(data["sizes"], product_image.attributes.get('sizes', {
                    'width': getattr(product_image, "width", '100%'),
                    'height': getattr(product_image, "height", '100%'),
                }))

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
