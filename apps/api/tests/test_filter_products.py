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

    def test_api_url_filter_by_results_count(self):
        """Test for proxy URL filtering by results=."""
        http = httplib2.Http()

        resp, content = http.request(self.api_url, 'GET', headers=self.headers)

        products = json.loads(content)
        unfiltered_len = len(products)

        resp, content = http.request(self.api_url + '?results=1', 'GET',
                                     headers=self.headers)

        products = json.loads(content)
        filtered_len = len(products)

        self.assertGreaterEqual(unfiltered_len, filtered_len)

    def test_api_url_filter_by_defined_keys(self):
        """Test for proxy URL filtering by url, rescrape, and sku, defined in

        docs: https://github.com/Willet/planning/blob/master/architecture/design-docs/contentgraph/product-api.md#search-able-attributes

        or

        HASH_FIELDS: https://github.com/Willet/ContentGraph/blob/715ad6395e3e0ff5489f45918c3dfc6b4811da47/contentgraph-api/src/main/java/com/willetinc/contentgraph/model/Product.java#L69

        """
        http = httplib2.Http()

        resp, content = http.request(self.api_url, 'GET', headers=self.headers)

        products = json.loads(content)
        unfiltered_len = len(products)

        resp, content = http.request(self.api_url + '?url=blah', 'GET',
                                     headers=self.headers)

        products = json.loads(content)
        filtered_len = len(products)

        # test for zero products on invalid url
        self.assertEqual(filtered_len, 0)

        resp, content = http.request(self.api_url + '?url=http://www.gap.com/products/P351401.jsp', 'GET',
                                     headers=self.headers)

        products = json.loads(content)
        filtered_len = len(products)

        # test for one product on valid url
        self.assertEqual(filtered_len, 1)

        resp, content = http.request(self.api_url + '?rescrape=false', 'GET',
                                     headers=self.headers)

        products = json.loads(content)
        filtered_len = len(products)

        # products not needing rescrape are strictly fewer than all products
        self.assertLessEqual(filtered_len, unfiltered_len)

        resp, content = http.request(self.api_url + '?sku=351401', 'GET',
                                     headers=self.headers)

        products = json.loads(content)
        filtered_len = len(products)

        # test for one product on valid sku
        self.assertEqual(filtered_len, 1)
