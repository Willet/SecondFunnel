"""Unit test"""

import json

from api_utils import ApiTestCase

import test_config as config


class ProductListProxyTestCase(ApiTestCase):
    """Test runner needs to be "logged in"."""

    def setUp(self):
        super(ProductListProxyTestCase, self).setUp()
        self.api_url = config.base_url + '/store/38/product/live'

    def test_api_url_returns_200(self):
        """Test for proxy URL returning something."""
        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        self.assertEqual(resp.status_code, '200')

    def test_api_url_is_json(self):
        """Test for proxy URL returning valid json."""
        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        self.assertEqual(resp.status_code, '200')

        try:
            products = json.loads(resp.content)
        except ValueError as err:
            self.assertEqual('is json', 'is not json')
