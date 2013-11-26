"""Unit test"""

import json
import mock

from apps.api.tests.utils import AuthenticatedTestCase, configure_mock_request

import test_config as config


class ProductListProxyTestCase(AuthenticatedTestCase):
    """Test runner needs to be "logged in"."""
    def setUp(self):
        super(ProductListProxyTestCase, self).setUp()
        self.api_url = config.base_url + '/store/38/product/live'

    @mock.patch('httplib2.Http.request')
    def test_api_url_returns_200(self, mock_request):
        """Test for proxy URL returning something."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/product/live/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        self.assertEqual(str(resp.status_code), '200')

    @mock.patch('httplib2.Http.request')
    def test_api_url_is_json(self, mock_request):
        """Test for proxy URL returning valid json."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/product/live/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        self.assertEqual(str(resp.status_code), '200')

        try:
            products = json.loads(resp.content)
        except ValueError as err:
            self.assertEqual('is json', 'is not json')

    @mock.patch('httplib2.Http.request')
    def test_api_url_is_transparent(self, mock_request):
        """Test for proxy URL returns exactly what ContentGraph returns."""
        mock_resp = {'a': 'b'}
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/product/live/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps(mock_resp)
            ),
        })

        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        try:
            products = json.loads(resp.content)
            self.assertEqual(products, mock_resp)
        except ValueError as err:
            self.assertEqual('is json', 'is not json')
