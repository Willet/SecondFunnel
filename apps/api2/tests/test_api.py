import datetime
from decimal import *
from django.core.urlresolvers import reverse
import json
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
import time


class APITest(APITestCase):
    fixtures = ['assets_api.json']

    def store_test(self):
        response = self.client.get(reverse('store-list'))
        self.assertEqual(len(response.data),2)
        store0 = response.data[0]
        store1 = response.data[1]

        self.assertEqual(store0['id'], 1)
        self.assertEqual(store0['staff'], [])
        self.assertEqual(store0['name'], u'MyStore')
        self.assertEqual(store0['description'], u'hi')
        self.assertEqual(store0['slug'], u'store_slug')
        self.assertEqual(store0['display_out_of_stock'], True)
        self.assertEqual(store0['default_theme'], None)
        self.assertEqual(store0['default_page'], None)
        self.assertEqual(store0['public_base_url'], u'http://gifts.mystore.com')

        self.assertEqual(store1['id'], 14)
        self.assertEqual(store1['staff'], [])
        self.assertEqual(store1['name'], u'MyOtherStore')
        self.assertEqual(store1['description'], u'hello')
        self.assertEqual(store1['slug'], u'store_slug')
        self.assertEqual(store1['display_out_of_stock'], False)
        self.assertEqual(store1['default_theme'], 2)
        self.assertEqual(store1['default_page'], 8)
        self.assertEqual(store1['public_base_url'], u'http://gifts2.mystore.com')

    def store_single_test(self):
        response = self.client.get(reverse('store-list')+'14/')
        store = response.data
        self.assertEqual(store['id'], 14)
        self.assertEqual(store['staff'], [])
        self.assertEqual(store['name'], u'MyOtherStore')
        self.assertEqual(store['description'], u'hello')
        self.assertEqual(store['slug'], u'store_slug')
        self.assertEqual(store['display_out_of_stock'], False)
        self.assertEqual(store['default_theme'], 2)
        self.assertEqual(store['default_page'], 8)
        self.assertEqual(store['public_base_url'], u'http://gifts2.mystore.com')

    def store_error_test(self):
        response = self.client.get(reverse('store-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def product_test(self):
        response = self.client.get(reverse('product-list'))
        self.assertEqual(len(response.data),4)
        product0 = response.data[0]
        product1 = response.data[1]
        product2 = response.data[2]
        product3 = response.data[3]

        self.assertEqual(product0['id'], 3)
        self.assertEqual(product0['name'], 'Default')
        self.assertEqual(product0['price'], Decimal('19.99'))
        self.assertEqual(product0['in_stock'], True)

        self.assertEqual(product1['id'], 12)
        self.assertEqual(product1['name'], 'Default2')
        self.assertEqual(product1['price'], Decimal('20.99'))
        self.assertEqual(product1['in_stock'], False)
        # test all keys of 1 product
        self.assertEqual(product2['id'], 15)
        self.assertEqual(product2['store'], 14)
        self.assertEqual(product2['name'], u'Default4')
        self.assertEqual(product2['description'], u'default default')
        self.assertEqual(product2['details'], u'<li>blah blah</li>')
        self.assertEqual(product2['url'], u'www.google.com/product')
        self.assertEqual(product2['sku'], u'1234')
        self.assertEqual(product2['price'], Decimal('29.99'))
        self.assertEqual(product2['sale_price'], Decimal('9.99'))
        self.assertEqual(product2['currency'], u'$')
        self.assertEqual(product2['default_image'], 11)
        self.assertEqual(product2['last_scraped_at'], None)
        self.assertEqual(product2['in_stock'], True)
        self.assertEqual(product2['attributes'], '{}')
        self.assertEqual(product2['similar_products'], [])

        self.assertEqual(product3['id'], 13)
        self.assertEqual(product3['name'], 'Default3')
        self.assertEqual(product3['price'], Decimal('21.99'))
        self.assertEqual(product3['in_stock'], True)

    def product_single_test(self):
        response = self.client.get(reverse('product-list')+'15/')
        product = response.data
        self.assertEqual(product['id'], 15)
        self.assertEqual(product['store'], 14)
        self.assertEqual(product['name'], u'Default4')
        self.assertEqual(product['description'], u'default default')
        self.assertEqual(product['details'], u'<li>blah blah</li>')
        self.assertEqual(product['url'], u'www.google.com/product')
        self.assertEqual(product['sku'], u'1234')
        self.assertEqual(product['price'], Decimal('29.99'))
        self.assertEqual(product['sale_price'], Decimal('9.99'))
        self.assertEqual(product['currency'], u'$')
        self.assertEqual(product['default_image'], 11)
        self.assertEqual(product['last_scraped_at'], None)
        self.assertEqual(product['in_stock'], True)
        self.assertEqual(product['attributes'], '{}')
        self.assertEqual(product['similar_products'], [])

    def product_error_test(self):
        response = self.client.get(reverse('product-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def content_test(self):
        response = self.client.get(reverse('content-list'))
        self.assertEqual(len(response.data),2)
        content0 = response.data[0]
        content1 = response.data[1]

        self.assertEqual(content0['id'], 6)
        self.assertEqual(content0['store'], 1)
        self.assertEqual(content0['name'], u"blah6")
        self.assertEqual(content0['description'], u"wah wah wah")
        self.assertEqual(content0['url'], u"/content.jpg")
        self.assertEqual(content0['source'], u"upload")
        self.assertEqual(content0['source_url'], u"www.google.com")
        self.assertEqual(content0['tagged_products'], [])
        self.assertEqual(content0['attributes'], '{}')
        self.assertEqual(content0['status'], u'needs-review')

        self.assertEqual(content1['id'], 16)
        self.assertEqual(content1['store'], 14)
        self.assertEqual(content1['name'], u"blah16")
        self.assertEqual(content1['description'], u"blah blah blah")
        self.assertEqual(content1['url'], u"/content.jpg")
        self.assertEqual(content1['source'], u"upload")
        self.assertEqual(content1['source_url'], u"www.facebook.com")
        self.assertEqual(content1['tagged_products'], [])
        self.assertEqual(content1['attributes'], '{}')
        self.assertEqual(content1['status'], u'approved')

    def content_single_test(self):
        response = self.client.get(reverse('content-list')+'6/')
        content = response.data
        self.assertEqual(content['id'], 6)
        self.assertEqual(content['store'], 1)
        self.assertEqual(content['name'], "blah6")
        self.assertEqual(content['description'], "wah wah wah")
        self.assertEqual(content['url'], u'/content.jpg')
        self.assertEqual(content['source'], u'upload')
        self.assertEqual(content['source_url'], u'www.google.com')
        self.assertEqual(content['tagged_products'], [])
        self.assertEqual(content['attributes'], '{}')
        self.assertEqual(content['status'], u'needs-review')

    def content_error_test(self):
        response = self.client.get(reverse('content-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def image_test(self):
        response = self.client.get(reverse('image-list'))
        self.assertEqual(len(response.data),1)
        image = response.data[0]
        self.assertEqual(image['id'], 6)
        self.assertEqual(image['name'], "blah6")
        self.assertEqual(image['description'], "wah wah wah")
        self.assertEqual(image['file_type'], u"jpg")
        self.assertEqual(image['file_checksum'], u"123456")
        self.assertEqual(image['width'], 350)
        self.assertEqual(image['height'], 600)
        self.assertEqual(image['dominant_color'], u"#FF1122")
        self.assertEqual(image['store'], 1)
        self.assertEqual(image['url'], u"/content.jpg")
        self.assertEqual(image['source'], u"upload")
        self.assertEqual(image['source_url'], u"www.google.com")
        self.assertEqual(image['tagged_products'], [])
        self.assertEqual(image['attributes'], '{}')
        self.assertEqual(image['status'], u'needs-review')

    def image_single_test(self):
        response = self.client.get(reverse('image-list')+'6/')
        image = response.data
        self.assertEqual(image['id'], 6)
        self.assertEqual(image['name'], "blah6")
        self.assertEqual(image['description'], "wah wah wah")
        self.assertEqual(image['file_type'], u"jpg")
        self.assertEqual(image['file_checksum'], u"123456")
        self.assertEqual(image['width'], 350)
        self.assertEqual(image['height'], 600)
        self.assertEqual(image['dominant_color'], u"#FF1122")
        self.assertEqual(image['store'], 1)
        self.assertEqual(image['url'], u"/content.jpg")
        self.assertEqual(image['source'], u"upload")
        self.assertEqual(image['source_url'], u"www.google.com")
        self.assertEqual(image['tagged_products'], [])
        self.assertEqual(image['attributes'], '{}')
        self.assertEqual(image['status'], u'needs-review')

    def image_error_test(self):
        response = self.client.get(reverse('image-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def gif_test(self):
        response = self.client.get(reverse('gif-list'))
        self.assertEqual(len(response.data),1)
        gif = response.data[0]
        self.assertEqual(gif['id'], 6)
        self.assertEqual(gif['gif_url'], u'test.com/gif1.gif')
        self.assertEqual(gif['name'], u"blah6")
        self.assertEqual(gif['description'], u"wah wah wah")
        self.assertEqual(gif['file_type'], u"jpg")
        self.assertEqual(gif['file_checksum'], u"123456")
        self.assertEqual(gif['width'], 350)
        self.assertEqual(gif['height'], 600)
        self.assertEqual(gif['dominant_color'], u"#FF1122")
        self.assertEqual(gif['store'], 1)
        self.assertEqual(gif['url'], u'/content.jpg')
        self.assertEqual(gif['source'], u'upload')
        self.assertEqual(gif['source_url'], u"www.google.com")
        self.assertEqual(gif['attributes'], '{}')
        self.assertEqual(gif['status'], u'needs-review')

    def gif_single_test(self):
        response = self.client.get(reverse('gif-list')+'6/')
        gif = response.data
        self.assertEqual(gif['id'], 6)
        self.assertEqual(gif['gif_url'], u'test.com/gif1.gif')
        self.assertEqual(gif['name'], u"blah6")
        self.assertEqual(gif['description'], u"wah wah wah")
        self.assertEqual(gif['file_type'], u"jpg")
        self.assertEqual(gif['file_checksum'], u"123456")
        self.assertEqual(gif['width'], 350)
        self.assertEqual(gif['height'], 600)
        self.assertEqual(gif['dominant_color'], u"#FF1122")
        self.assertEqual(gif['store'], 1)
        self.assertEqual(gif['url'], u'/content.jpg')
        self.assertEqual(gif['source'], u'upload')
        self.assertEqual(gif['source_url'], u"www.google.com")
        self.assertEqual(gif['attributes'], '{}')
        self.assertEqual(gif['status'], u'needs-review')

    def gif_error_test(self):
        response = self.client.get(reverse('gif-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def productimage_test(self):
        response = self.client.get(reverse('productimage-list'))
        self.assertEqual(len(response.data),2)
        pi0 = response.data[0]
        pi1 = response.data[1]

        self.assertEqual(pi0['id'], 4)
        self.assertEqual(pi0['product'], 13)
        self.assertEqual(pi0['url'], u'/image.jpg')
        self.assertEqual(pi0['original_url'], u'test.com/image.jpg')
        self.assertEqual(pi0['file_type'], u"jpg")
        self.assertEqual(pi0['file_checksum'], "123456")
        self.assertEqual(pi0['width'], 100)
        self.assertEqual(pi0['height'], 100)
        self.assertEqual(pi0['dominant_color'], u"#556677")
        self.assertEqual(json.loads(pi0['image_sizes']), {
          "h400": {
            "url": "http://images.secondfunnel.com/foo/h400/bar.jpg",
            "height": 400,
            },
            "master": {
              "url": "http://images.secondfunnel.com/foo/bar.jpg",
              "width": 640,
              "height": 480,
            },
          })
        self.assertEqual(pi0['attributes'], '{}')

        self.assertEqual(pi1['product'], 13)

    def productimage_single_test(self):
        response = self.client.get(reverse('productimage-list')+'11/')
        pi = response.data
        self.assertEqual(pi['id'], 11)
        self.assertEqual(pi['product'], 13)
        self.assertEqual(pi['url'], u'/another-image.jpg')
        self.assertEqual(pi['original_url'], u'test.com/another-image.jpg')
        self.assertEqual(pi['file_type'], u"jpg")
        self.assertEqual(pi['file_checksum'], "345678")
        self.assertEqual(pi['width'], 200)
        self.assertEqual(pi['height'], 200)
        self.assertEqual(pi['dominant_color'], u"#5500AA")
        self.assertEqual(json.loads(pi['image_sizes']), {
          "h400": {
            "url": "http://images.secondfunnel.com/foo/h400/bar.jpg",
            "height": 400,
          },
          "master": {
            "url": "http://images.secondfunnel.com/foo/bar.jpg",
            "width": 640,
            "height": 480,
          },
          "w400": {
            "url": "http://images.secondfunnel.com/foo/w400/bar.jpg",
            "width": 400,
            "height": 400,
          },
        })
        self.assertEqual(pi['attributes'], '{}')

    def productimage_error_test(self):
        response = self.client.get(reverse('productimage-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def video_test(self):
        response = self.client.get(reverse('video-list'))
        self.assertEqual(len(response.data),2)
        video = response.data[0]
        self.assertEqual(video['id'], 6)
        self.assertEqual(video['name'], u'blah6')
        self.assertEqual(video['description'], u'wah wah wah')
        self.assertEqual(video['player'], u'youtube')
        self.assertEqual(video['file_type'], u'jpg')
        self.assertEqual(video['file_checksum'], u"345678")
        self.assertEqual(video['original_id'], u'vid1originalID')
        self.assertEqual(video['store'], 1)
        self.assertEqual(video['url'], u'/content.jpg')
        self.assertEqual(video['source'], u'upload')
        self.assertEqual(video['source_url'], u"www.google.com")
        self.assertEqual(video['tagged_products'], [])
        self.assertEqual(video['attributes'], '{}')
        self.assertEqual(video['status'], u'needs-review')

    def video_single_test(self):
        response = self.client.get(reverse('video-list')+'16/')
        video = response.data
        self.assertEqual(video['id'], 16)
        self.assertEqual(video['name'], u'blah16')
        self.assertEqual(video['description'], u'blah blah blah')
        self.assertEqual(video['player'], u'facebook')
        self.assertEqual(video['file_type'], u"png")
        self.assertEqual(video['file_checksum'], u"987654")
        self.assertEqual(video['original_id'], u'vid2originalID')
        self.assertEqual(video['store'], 14)
        self.assertEqual(video['url'], u'/content.jpg')
        self.assertEqual(video['source'], u'upload')
        self.assertEqual(video['source_url'], u"www.facebook.com")
        self.assertEqual(video['tagged_products'], [])
        self.assertEqual(video['attributes'], '{}')
        self.assertEqual(video['status'], u'approved')

    def video_error_test(self):
        response = self.client.get(reverse('video-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def page_test(self):
        response = self.client.get(reverse('page-list'))
        self.assertEqual(len(response.data),2)
        page0 = response.data[0]
        page1 = response.data[1]

        self.assertEqual(page0['id'], 8)
        self.assertEqual(page0['store'], 1)
        self.assertEqual(page0['name'], u'TestPage')
        self.assertEqual(page0['theme'], None)
        self.assertEqual(page0['theme_settings'], '{}')
        self.assertEqual(page0['dashboard_settings'], '{}')
        self.assertEqual(page0['campaign'], None)
        self.assertEqual(page0['description'], None)
        self.assertEqual(page0['url_slug'], u'test_page')
        self.assertEqual(page0['legal_copy'], None)
        self.assertEqual(page0['last_published_at'], None)
        self.assertEqual(page0['feed'], None)

        self.assertEqual(page1['id'], 17)
        self.assertEqual(page1['store'], 1)
        self.assertEqual(page1['name'], u'TestPage')
        self.assertEqual(page1['theme'], None)
        self.assertEqual(page1['theme_settings'], '{}')
        self.assertEqual(page1['dashboard_settings'], '{}')
        self.assertEqual(page1['campaign'], None)
        self.assertEqual(page1['description'], None)
        self.assertEqual(page1['url_slug'], u'other_test_page')
        self.assertEqual(page1['legal_copy'], None)
        self.assertEqual(page1['last_published_at'], None)
        self.assertEqual(page1['feed'], None)

    def page_single_test(self):
        response = self.client.get(reverse('page-list')+'17/')
        page = response.data
        self.assertEqual(page['id'], 17)
        self.assertEqual(page['store'], 1)
        self.assertEqual(page['name'], u'TestPage')
        self.assertEqual(page['theme'], None)
        self.assertEqual(page['theme_settings'], '{}')
        self.assertEqual(page['dashboard_settings'], '{}')
        self.assertEqual(page['campaign'], None)
        self.assertEqual(page['description'], None)
        self.assertEqual(page['url_slug'], u'other_test_page')
        self.assertEqual(page['legal_copy'], None)
        self.assertEqual(page['last_published_at'], None)
        self.assertEqual(page['feed'], None)

    def page_error_test(self):
        response = self.client.get(reverse('page-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def tile_test(self):
        response = self.client.get(reverse('tile-list'))
        self.assertEqual(len(response.data),3)
        tile0 = response.data[0]
        tile1 = response.data[1]
        tile2 = response.data[2]

        self.assertEqual(tile0['id'], 10)
        self.assertEqual(tile0['feed'], 9)
        self.assertEqual(tile0['template'], u'default')
        self.assertEqual(tile0['products'], [])
        self.assertEqual(tile0['priority'], 0)
        self.assertEqual(tile0['clicks'], 0)
        self.assertEqual(tile0['views'], 0)
        self.assertEqual(tile0['placeholder'], False)
        self.assertEqual(tile0['in_stock'], True)
        self.assertEqual(tile0['attributes'], '{}')

        self.assertEqual(tile1['id'], 11)
        self.assertEqual(tile1['feed'], 9)
        self.assertEqual(tile1['template'], u'default')
        self.assertEqual(tile1['products'], [])
        self.assertEqual(tile1['priority'], 0)
        self.assertEqual(tile1['clicks'], 0)
        self.assertEqual(tile1['views'], 0)
        self.assertEqual(tile1['placeholder'], False)
        self.assertEqual(tile1['in_stock'], True)
        self.assertEqual(tile1['attributes'], '{}')

        self.assertEqual(tile2['id'], 13)
        self.assertEqual(tile2['feed'], 13)
        self.assertEqual(tile2['template'], u'default')
        self.assertEqual(tile2['products'], [])
        self.assertEqual(tile2['priority'], 0)
        self.assertEqual(tile2['clicks'], 0)
        self.assertEqual(tile2['views'], 0)
        self.assertEqual(tile2['placeholder'], False)
        self.assertEqual(tile2['in_stock'], True)
        self.assertEqual(tile2['attributes'], '{}')

    def tile_single_test(self):
        response = self.client.get(reverse('tile-list')+'11/')
        tile = response.data
        self.assertEqual(tile['id'], 11)
        self.assertEqual(tile['feed'], 9)
        self.assertEqual(tile['template'], u'default')
        self.assertEqual(tile['products'], [])
        self.assertEqual(tile['priority'], 0)
        self.assertEqual(tile['clicks'], 0)
        self.assertEqual(tile['views'], 0)
        self.assertEqual(tile['placeholder'], False)
        self.assertEqual(tile['in_stock'], True)
        self.assertEqual(tile['attributes'], '{}')
        self.assertEqual(tile['feed'],9)

    def tile_error_test(self):
        response = self.client.get(reverse('tile-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def feed_test(self):
        response = self.client.get(reverse('feed-list'))
        self.assertEqual(len(response.data),4)
        feed0 = response.data[0]
        feed1 = response.data[1]

        self.assertEqual(feed0['id'],9)
        self.assertEqual(feed0['feed_algorithm'],"magic")
        self.assertEqual(feed0['feed_ratio'],Decimal('0.20'))

        self.assertEqual(feed1['id'],13)
        self.assertEqual(feed1['feed_algorithm'],"priority")
        self.assertEqual(feed1['feed_ratio'],Decimal('0.6'))

    def feed_single_test(self):
        response = self.client.get(reverse('feed-list')+'18/')
        self.assertEqual(response.data['feed_algorithm'],"non-priority")
        self.assertEqual(response.data['feed_ratio'],Decimal('0.3'))

    def feed_error_test(self):
        response = self.client.get(reverse('feed-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')

    def category_test(self):
        response = self.client.get(reverse('category-list'))
        self.assertEqual(len(response.data),2)
        category0 = response.data[0]
        category1 = response.data[1]

        self.assertEqual(category0['name'],u'TestCategory')
        self.assertEqual(category0['id'],7)

        self.assertEqual(category1['name'],u'TestCategory2')
        self.assertEqual(category1['id'],8)

    def category_single_test(self):
        response = self.client.get(reverse('category-list')+'8/')
        self.assertEqual(response.data['name'],u'TestCategory2')
        self.assertEqual(response.data['id'],8)

    def category_error_test(self):
        response = self.client.get(reverse('category-list')+'100/')
        self.assertEqual(response.data,{u'detail': u'Not found'})
        self.assertEqual(response.data[u'detail'],u'Not found')
