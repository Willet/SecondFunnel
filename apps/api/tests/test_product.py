import json
import mock
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request


class AuthenticatedProductTestSuite(AuthenticatedResourceTestCase):
    @mock.patch('httplib2.Http.request')
    def test_delete(self, mock_request):
        """checks if the proxy relays the delete call correctly."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/product/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        # TODO: Make URL pattern a 'constant' in somewhere relevant
        response = self.api_client.post(
            '/graph/v1/store/1/page/1/product/1',
            format='json'
        )

        self.assertHttpOK(response)

    # TODO: Should this be broken into smaller tests?
    # TODO: Should mock request responses be kept at top of test file?
    @mock.patch('httplib2.Http.request')
    def test_api_url_filter_by_defined_keys(self, mock_request):
        """Test for proxy URL filtering by url, rescrape, and sku, defined in

        docs: https://github.com/Willet/planning/blob/master/architecture/design-docs/contentgraph/product-api.md#search-able-attributes

        or

        HASH_FIELDS: https://github.com/Willet/ContentGraph/blob/715ad6395e3e0ff5489f45918c3dfc6b4811da47/contentgraph-api/src/main/java/com/willetinc/contentgraph/model/Product.java#L69

        """
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/product/live$': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [1, 2, 3] # Not represenative of real data
                })
            ),
            r'store/\d+/product/live\?url=blah$': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': []
                })
            ),
            r'store/\d+/product/live\?url=https?://.*$': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [1]
                })
            ),
            r'store/\d+/product/live\?rescrape=false$': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [1, 2]
                })
            ),
            r'store/\d+/product/live\?sku=\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [2]
                })
            ),
        })

        response = self.api_client.get(
            '/graph/v1/store/38/product/live',
            format='json'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)

        # Get initial count of all products
        count_live = len(json.loads(response.content).get('results'))

        response = self.api_client.get(
            '/graph/v1/store/38/product/live?url=blah',
            format='json'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)

        count_bad_url = len(json.loads(response.content).get('results'))

        # Verify that invalid URL yields no results
        self.assertEqual(count_bad_url, 0)

        # such url
        response = self.api_client.get(
            '/graph/v1/store/38/product/live'
            '?url=http://www.gap.com/products/P351401.jsp',
            format='json'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)

        count_single_result = len(json.loads(response.content).get('results'))

        # Verify that filtering on URL yields one result
        self.assertEqual(count_single_result, 1)

        response = self.api_client.get(
            '/graph/v1/store/38/product/live?rescrape=false',
            format='json'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)

        count_non_rescraped = len(json.loads(response.content).get('results'))

        # All products >= products[rescrape=false]
        self.assertGreaterEqual(count_live, count_non_rescraped)

        response = self.api_client.get(
            '/graph/v1/store/38/product/live?sku=351401',
            format='json'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)

        count_sku = len(json.loads(response.content).get('results'))

        # test for one product on valid sku
        self.assertEqual(count_sku, 1)

    @mock.patch('httplib2.Http.request')
    def test_api_url_get_products(self, mock_request):
        """Test for proxy URL filtering by results=."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/product$': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [
                        {'id': 2},
                        {'id': 1},
                        {'id': 3},
                    ]
                })
            ),
            r'store/\d+/page/\d+/product\?order=ascending$': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [
                        {'id': 1},
                        {'id': 2},
                        {'id': 3},
                    ]
                })
            ),
            r'store/\d+/page/\d+/product\?order=descending': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [
                        {'id': 3},
                        {'id': 2},
                        {'id': 1},
                    ]
                })
            ),
        })

        response = self.api_client.get(
            '/graph/v1/store/38/page/97/product',
            format='json'
        )

        products = json.loads(response.content).get('results')

        response = self.api_client.get(
            '/graph/v1/store/38/page/97/product?order=ascending',
            format='json'
        )

        ascending_products = json.loads(response.content).get('results')

        # Ascending should always be less than or equal
        self.assertLessEqual(
            ascending_products[0].get('id'),
            products[0].get('id')
        )

        response = self.api_client.get(
            '/graph/v1/store/38/page/97/product?order=descending',
            format='json'
        )

        descending_products = json.loads(response.content).get('results')

        # Descending should always be greater than or equal
        self.assertGreaterEqual(
            descending_products[0].get('id'),
            products[0].get('id')
        )

        self.assertGreaterEqual(
            descending_products[0].get('id'),
            ascending_products[0].get('id')
        )

        self.assertGreaterEqual(
            descending_products[0].get('id'),
            ascending_products[0].get('id')
        )