import json

from apps.api.tests.utils import AuthenticatedTestCase

import test_config as config


class ProductListProxyTestCase(AuthenticatedTestCase):
    """Test runner needs to be "logged in"."""
    def setUp(self):
        super(ProductListProxyTestCase, self).setUp()
        self.test_url = '%s/store/38/page/97/product' % config.base_url

    def test_api_url_get_products(self):
        """Test for proxy URL filtering by results=."""
        resp = self.api_client.get(self.test_url)
        unfiltered_products = json.loads(resp.content)['results']

        resp = self.api_client.get(self.test_url + '?order=ascending')
        filtered_products = json.loads(resp.content)['results']

        # sorted entries have lower id for its first product
        # (unless the two products are the same)
        if len(unfiltered_products) >= 1 and len(filtered_products) >= 1:
            self.assertGreaterEqual(unfiltered_products[0]['id'],
                                    filtered_products[0]['id'])

        resp = self.api_client.get(self.test_url + '?order=descending')
        filtered_products = json.loads(resp.content)['results']

        # sorted entries have higher id for its first product
        # (unless the two products are the same)
        if len(unfiltered_products) >= 1 and len(filtered_products) >= 1:
            self.assertLessEqual(unfiltered_products[0]['id'],
                                 filtered_products[0]['id'])
