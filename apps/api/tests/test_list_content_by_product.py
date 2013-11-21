"""Unit test"""

import json

from api_utils import ApiTestCase

import test_config as config


class ProductListProxyTestCase(ApiTestCase):
    """Test runner needs to be "logged in"."""

    def setUp(self):
        super(ProductListProxyTestCase, self).setUp()
        self.api_url = config.base_url + '/store/38/page/97/content/by-id'

    def test_api_url_returns_200(self):
        """Test for proxy URL returning something."""
        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        self.assertEqual(str(resp.status_code), '200')

    def test_api_url_is_json(self):
        """Test for proxy URL returning valid json."""
        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        self.assertEqual(str(resp.status_code), '200')

        try:
            products = json.loads(resp.content)
        except ValueError as err:
            self.assertEqual('is json', 'is not json')

    def test_api_url_has_product_keys(self):
        """Test for proxy URL returning valid json format."""
        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        # "all keys are numeric, but are kept as strings because json"
        is_valid = all([str(int(x)) == x for x in \
                        json.loads(resp.content)['results'].keys()])

        self.assertTrue(is_valid)
