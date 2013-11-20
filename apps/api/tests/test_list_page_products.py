import httplib2
import json
import time

from django.conf import settings
from tastypie.test import ResourceTestCase

import test_config as config


class ProductListProxyTestCase(ResourceTestCase):
    """Test runner needs to be "logged in"."""
    def setUp(self):
        self.test_url = '%s/store/38/page/97/product' % config.base_url

        super(ProductListProxyTestCase, self).setUp()

    def get_credentials(self):
        """TODO"""
        resp = self.api_client.post(config.login_url, format="json", data=config.valid_login)
        return self.create_basic(username=config.valid_login['username'],
                                 password=config.valid_login['password'])

    def test_api_url_get_products(self):
        """Test for proxy URL filtering by results=."""
        resp = self.api_client.get(self.test_url)
        unfiltered_products = json.loads(resp.content)['results']

        resp = self.api_client.get(self.test_url + '?order=ascending')
        filtered_products = json.loads(resp.content)['results']

        # sorted entries have lower id for its first product
        self.assertGreater(unfiltered_products[0]['id'], filtered_products[0]['id'])

        resp = self.api_client.get(self.test_url + '?order=descending')
        filtered_products = json.loads(resp.content)['results']

        # sorted entries have higher id for its first product
        self.assertLess(unfiltered_products[0]['id'], filtered_products[0]['id'])
