from django.core.urlresolvers import reverse
import datetime
import time
from decimal import *

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

class APITest(APITestCase):
    fixtures = ['assets_api.json']

    def store_test(self):
        response = self.client.get(reverse('store-list'))
        self.assertEqual(len(response.data),2)
        self.assertEqual(response.data,[{
            'id': 1, 
            'staff': [], 
            'name': u'MyStore', 
            'description': u'', 
            'slug': u'store_slug', 
            'display_out_of_stock': False, 
            'default_theme': None, 
            'default_page': None, 
            'public_base_url': u'gifts.mystore.com'
         }, {
            'id': 14, 
            'staff': [], 
            'name': u'MyOtherStore', 
            'description': u'', 
            'slug': u'store_slug', 
            'display_out_of_stock': False, 
            'default_theme': None, 
            'default_page': None, 
            'public_base_url': u'gifts2.mystore.com'
        }])

    def store_single_test(self):
        response = self.client.get(reverse('store-list')+'14/')
        self.assertEqual(response.data,{
            'id': 14, 
            'staff': [], 
            'name': u'MyOtherStore', 
            'description': u'', 
            'slug': u'store_slug', 
            'display_out_of_stock': False, 
            'default_theme': None,
            'default_page': None, 
            'public_base_url': u'gifts2.mystore.com'
        })
        self.assertEqual(response.data['name'],u'MyOtherStore')

    def store_error_test(self):
        response = self.client.get(reverse('store-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def product_test(self):
        response = self.client.get(reverse('product-list'))
        self.assertEqual(len(response.data),4)
        self.assertEqual(response.data[0]['id'],3)
        self.assertEqual(response.data[0]['name'],'Default')
        self.assertEqual(response.data[0]['price'],Decimal('19.99'))
        self.assertEqual(response.data[0]['in_stock'],True)
        self.assertEqual(response.data[1]['id'],12)
        self.assertEqual(response.data[1]['name'],'Default2')
        self.assertEqual(response.data[1]['price'],Decimal('20.99'))
        self.assertEqual(response.data[1]['in_stock'],False)
        self.assertEqual(response.data[2]['id'],15)
        self.assertEqual(response.data[2]['name'],'Default4')
        self.assertEqual(response.data[2]['price'],Decimal('29.99'))
        self.assertEqual(response.data[2]['in_stock'],True)
        self.assertEqual(response.data[3]['id'],13)
        self.assertEqual(response.data[3]['name'],'Default3')
        self.assertEqual(response.data[3]['price'],Decimal('21.99'))
        self.assertEqual(response.data[3]['in_stock'],True)

    def product_single_test(self):
        response = self.client.get(reverse('product-list')+'15/')
        self.assertEqual(response.data,{
              'id': 15, 
              'store': 14, 
              'name': u'Default4', 
              'description': u'', 
              'details': u'', 
              'url': u'', 
              'sku': u'', 
              'price': Decimal('29.99'), 
              'sale_price': None, 
              'currency': u'$', 
              'default_image': None, 
              'last_scraped_at': None, 
              'in_stock': True, 
              'attributes': '{}', 
              'similar_products': []
            })
        self.assertEqual(response.data['price'],Decimal('29.99'))

    def product_error_test(self):
        response = self.client.get(reverse('product-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def content_test(self):
        response = self.client.get(reverse('content-list'))
        self.assertEqual(len(response.data),2)
        self.assertEqual(response.data,[{
              'id': 6, 
              'store': 1, 
              'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 
              'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            }, {
              'id': 16, 
              'store': 14, 
              'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 
              'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            }])

    def content_single_test(self):
        response = self.client.get(reverse('content-list')+'6/')
        self.assertEqual(response.data,{
              'id': 6,
              'store': 1, 
              'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 
              'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            })
        self.assertEqual(response.data['source_url'],u'/content.jpg')

    def content_error_test(self):
        response = self.client.get(reverse('content-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def image_test(self):
        response = self.client.get(reverse('image-list'))
        self.assertEqual(len(response.data),1)
        self.assertEqual(response.data,[{
              'id': 6, 
              'name': None, 
              'description': None, 
              'original_url': u'test.com/image.jpg', 
              'file_type': None, 
              'file_checksum': None, 
              'width': None, 
              'height': None, 
              'dominant_color': None, 
              'store': 1, 
              'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 
              'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            }])

    def image_single_test(self):
        response = self.client.get(reverse('image-list')+'6/')
        self.assertEqual(response.data,{
              'id': 6, 
              'name': None, 
              'description': None, 
              'original_url': u'test.com/image.jpg', 
              'file_type': None, 
              'file_checksum': None, 
              'width': None, 
              'height': None, 
              'dominant_color': None, 
              'store': 1, 
              'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 
              'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            })
        self.assertEqual(response.data['original_url'],u'test.com/image.jpg')

    def image_error_test(self):
        response = self.client.get(reverse('image-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def gif_test(self):
        response = self.client.get(reverse('gif-list'))
        self.assertEqual(len(response.data),1)
        self.assertEqual(response.data,[{
              'id': 6, 
              'gif_url': u'test.com/gif1.gif', 
              'name': None, 
              'description': None, 
              'original_url': u'test.com/image.jpg', 
              'file_type': None, 
              'file_checksum': None, 
              'width': None, 
              'height': None, 
              'dominant_color': None, 
              'store': 1, 'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            }])

    def gif_single_test(self):
        response = self.client.get(reverse('gif-list')+'6/')
        self.assertEqual(response.data,{
              'id': 6, 
              'gif_url': u'test.com/gif1.gif', 
              'name': None, 
              'description': None, 
              'original_url': u'test.com/image.jpg', 
              'file_type': None, 
              'file_checksum': None, 
              'width': None, 
              'height': None, 
              'dominant_color': None, 
              'store': 1, 'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            })
        self.assertEqual(response.data['gif_url'],u'test.com/gif1.gif')

    def gif_error_test(self):
        response = self.client.get(reverse('gif-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def productimage_test(self):
        response = self.client.get(reverse('productimage-list'))
        self.assertEqual(len(response.data),2)
        self.assertEqual(response.data[0],{
              'id': 4, 
              'product': None, 
              'url': u'/image.jpg', 
              'original_url': u'test.com/image.jpg', 
              'file_type': None, 
              'file_checksum': None, 
              'width': None, 
              'height': None, 
              'dominant_color': None, 
              'image_sizes': '{}', 
              'attributes': '{}'
            })
        self.assertEqual(response.data[1]['product'],13)

    def productimage_single_test(self):
        response = self.client.get(reverse('productimage-list')+'4/')
        self.assertEqual(response.data,{
              'id': 4, 
              'product': None, 
              'url': u'/image.jpg', 
              'original_url': u'test.com/image.jpg', 
              'file_type': None, 
              'file_checksum': None, 
              'width': None, 
              'height': None, 
              'dominant_color': None, 
              'image_sizes': '{}', 
              'attributes': '{}'
            })
        self.assertEqual(response.data['original_url'],u'test.com/image.jpg')

    def productimage_error_test(self):
        response = self.client.get(reverse('productimage-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def video_test(self):
        response = self.client.get(reverse('video-list'))
        self.assertEqual(len(response.data),2)
        self.assertEqual(response.data[0],{
              'id': 6, 
              'name': u'video1', 
              'caption': u'captionVid1', 
              'username': u'user1', 
              'description': u'video1description', 
              'player': u'youtube', 
              'file_type': None, 
              'file_checksum': None, 
              'original_id': u'vid1originalID', 
              'store': 1, 'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 
              'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            })

    def video_single_test(self):
        response = self.client.get(reverse('video-list')+'16/')
        self.assertEqual(response.data,{
              'id': 16, 
              'name': u'video2', 
              'caption': u'captionVid2', 
              'username': u'user2', 
              'description': u'video2description', 
              'player': u'facebook', 
              'file_type': None, 
              'file_checksum': None, 
              'original_id': u'vid2originalID', 
              'store': 14, 
              'url': u'/content.jpg', 
              'source': u'upload', 
              'source_url': u'/content.jpg', 
              'author': None, 
              'tagged_products': [], 
              'attributes': '{}', 
              'status': u'needs-review'
            })
        self.assertEqual(response.data['caption'],u'captionVid2')

    def video_error_test(self):
        response = self.client.get(reverse('video-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def page_test(self):
        response = self.client.get(reverse('page-list'))
        self.assertEqual(len(response.data),2)
        self.assertEqual(response.data,[{
              'id': 8, 
              'store': 1, 
              'name': u'TestPage', 
              'theme': None, 
              'theme_settings': '{}', 
              'dashboard_settings': '{}', 
              'campaign': None, 
              'description': None, 
              'url_slug': u'test_page', 
              'legal_copy': None, 
              'last_published_at': None, 
              'feed': None
            }, {
              'id': 17, 
              'store': 1, 
              'name': u'TestPage', 
              'theme': None, 
              'theme_settings': '{}', 
              'dashboard_settings': '{}', 
              'campaign': None, 
              'description': None, 
              'url_slug': u'other_test_page', 
              'legal_copy': None, 
              'last_published_at': None, 
              'feed': None
            }])

    def page_single_test(self):
        response = self.client.get(reverse('page-list')+'17/')
        self.assertEqual(response.data,{
              'id': 17, 
              'store': 1, 
              'name': u'TestPage', 
              'theme': None, 
              'theme_settings': '{}', 
              'dashboard_settings': '{}', 
              'campaign': None, 
              'description': None, 
              'url_slug': u'other_test_page', 
              'legal_copy': None, 
              'last_published_at': None, 
              'feed': None
            })
        self.assertEqual(response.data['name'],u'TestPage')

    def page_error_test(self):
        response = self.client.get(reverse('page-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def tile_test(self):
        response = self.client.get(reverse('tile-list'))
        self.assertEqual(len(response.data),3)
        self.assertEqual(response.data,[{
              'id': 10, 
              'feed': 9, 
              'template': u'default', 
              'products': [], 
              'priority': 0, 
              'clicks': 0, 
              'views': 0, 
              'placeholder': False, 
              'in_stock': True, 
              'attributes': '{}'
            }, {
              'id': 11, 
              'feed': 9, 
              'template': u'default', 
              'products': [], 
              'priority': 0, 
              'clicks': 0, 
              'views': 0, 
              'placeholder': False, 
              'in_stock': True, 'attributes': '{}'
            }, {
              'id': 13, 
              'feed': 13, 
              'template': u'default', 
              'products': [], 
              'priority': 0, 
              'clicks': 0, 
              'views': 0, 
              'placeholder': False, 
              'in_stock': True, 
              'attributes': '{}'
            }])

    def tile_single_test(self):
        response = self.client.get(reverse('tile-list')+'11/')
        self.assertEqual(response.data,{
              'id': 11, 
              'feed': 9, 
              'template': u'default', 
              'products': [], 
              'priority': 0, 
              'clicks': 0, 
              'views': 0, 
              'placeholder': False, 
              'in_stock': True, 'attributes': '{}'
            })
        self.assertEqual(response.data['feed'],9)

    def tile_error_test(self):
        response = self.client.get(reverse('tile-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')
