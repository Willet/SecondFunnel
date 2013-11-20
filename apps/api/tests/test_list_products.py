""""""


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

    def test_api_url_returns_200(self):
        """Test for proxy URL returning something."""
        http = httplib2.Http()

        resp, content = http.request(self.api_url, 'GET', headers=self.headers)

        self.assertEqual(resp.status, 200)

    def test_api_url_is_json(self):
        """Test for proxy URL returning valid json."""
        http = httplib2.Http()

        resp, content = http.request(self.api_url, 'GET', headers=self.headers)

        try:
            products = json.loads(content)
        except ValueError as err:
            self.assertEqual('is json', 'is not json')
