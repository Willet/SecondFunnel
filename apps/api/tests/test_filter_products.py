import json

from api_utils import ApiTestCase

import test_config as config


class ProductListProxyTestCase(ApiTestCase):
    """Test runner needs to be "logged in"."""
    def setUp(self):
        super(ProductListProxyTestCase, self).setUp()
        self.api_url = config.base_url + '/store/38/product/live'

    def test_api_url_filter_by_results_count(self):
        """Test for proxy URL filtering by results=."""
        resp = self.api_client.get(self.api_url,
                                   format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        products = json.loads(resp.content)['results']
        unfiltered_len = len(products)

        resp = self.api_client.get(self.api_url + '?results=1',
                                   format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        products = json.loads(resp.content)['results']
        filtered_len = len(products)

        self.assertGreaterEqual(unfiltered_len, filtered_len)

    def test_api_url_filter_by_defined_keys(self):
        """Test for proxy URL filtering by url, rescrape, and sku, defined in

        docs: https://github.com/Willet/planning/blob/master/architecture/design-docs/contentgraph/product-api.md#search-able-attributes

        or

        HASH_FIELDS: https://github.com/Willet/ContentGraph/blob/715ad6395e3e0ff5489f45918c3dfc6b4811da47/contentgraph-api/src/main/java/com/willetinc/contentgraph/model/Product.java#L69

        """
        resp = self.api_client.get(self.api_url,
                                   format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        products = json.loads(resp.content)['results']
        unfiltered_len = len(products)

        # no such url
        resp = self.api_client.get(self.api_url + '?url=blah',
                                   format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        products = json.loads(resp.content)['results']
        filtered_len = len(products)

        # test for zero products on invalid url
        self.assertEqual(filtered_len, 0)

        # such url
        resp = self.api_client.get(
            self.api_url + '?url=http://www.gap.com/products/P351401.jsp',
            format='json', authentication=self.get_credentials(),
            headers=self.headers)

        products = json.loads(resp.content)['results']
        filtered_len = len(products)

        # test for one product on valid url
        self.assertEqual(filtered_len, 1)

        resp = self.api_client.get(
            self.api_url + '?rescrape=false',
            format='json', authentication=self.get_credentials(),
            headers=self.headers)

        products = json.loads(resp.content)['results']
        filtered_len = len(products)

        # products not needing rescrape are strictly fewer than all products
        self.assertLessEqual(filtered_len, unfiltered_len)

        # by sku
        resp = self.api_client.get(
            self.api_url + '?sku=351401',
            format='json', authentication=self.get_credentials(),
            headers=self.headers)

        products = json.loads(resp.content)['results']
        filtered_len = len(products)

        # test for one product on valid sku
        self.assertEqual(filtered_len, 1)
