import httplib2
import json

from django.test import TestCase


class ProductListProxyTestCase(TestCase):
    """Test runner needs to be "logged in"."""
    def setUp(self):
        self.api_root = 'http://127.0.0.1:9000/graph/v1'
        self.api_url = self.api_root + '/store/38/product/live'
        self.headers = {'cache-control': 'no-cache',
                        'ApiKey': 'secretword',
                        'Content-type': 'application/json',
                        }

    def test_api_url_sort(self):
        """Test for proxy URL filtering by results=."""
        http = httplib2.Http()

        resp, content = http.request(self.api_url, 'GET', headers=self.headers)

        unfiltered_products = json.loads(content)['results']

        resp, content = http.request(self.api_url + '?order=ascending', 'GET',
                                     headers=self.headers)

        filtered_products = json.loads(content)['results']
        
        # sorted entries have lower id for its first product
        self.assertGreater(unfiltered_products[0]['id'], filtered_products[0]['id'])

        resp, content = http.request(self.api_url + '?order=descending', 'GET',
                                     headers=self.headers)

        filtered_products = json.loads(content)['results']

        # sorted entries have higher id for its first product
        self.assertLess(unfiltered_products[0]['id'], filtered_products[0]['id'])
