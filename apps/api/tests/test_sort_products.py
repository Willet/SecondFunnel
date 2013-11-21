import json

from api_utils import ApiTestCase

import test_config as config


class ProductListProxyTestCase(ApiTestCase):
    """Test runner needs to be "logged in"."""

    def setUp(self):
        super(ProductListProxyTestCase, self).setUp()
        self.api_url = config.base_url + '/store/38/product/live'

    def test_api_url_sort(self):
        """Test for proxy URL ordering=a/descending."""

        resp = self.api_client.get(self.api_url + '?order=ascending',
                                   format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        ascending_products = json.loads(resp.content)['results']
        
        resp = self.api_client.get(self.api_url + '?order=descending',
                                   format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        descending_products = json.loads(resp.content)['results']

        if len(ascending_products) >= 1 and len(descending_products) >= 1:
            # sort is active and is working
            self.assertLess(int(ascending_products[0]['id']),
                            int(descending_products[0]['id']))
