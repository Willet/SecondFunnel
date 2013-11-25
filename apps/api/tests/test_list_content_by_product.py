import json
import mock

from django.contrib.auth.models import User
from django.test import RequestFactory

from apps.api.tests.utils import AuthenticatedTestCase, configure_mock_request
from apps.api.views import get_suggested_content_by_page

import test_config as config


class ProductListProxyTestCase(AuthenticatedTestCase):
    """Test runner needs to be "logged in"."""

    def setUp(self):
        super(ProductListProxyTestCase, self).setUp()
        self.api_url = config.base_url + '/store/38/page/97/content/suggested'

        if not getattr(self, 'mock_resp', None):
            req_factory = RequestFactory()
            req = req_factory.get(self.api_url)
            req.user = User.objects.get(username='gap')

            self.mock_resp = get_suggested_content_by_page(
                req, 38, 97).content
            self.mock_ids = json.dumps({"results":[
                "65","64","63","62","61","60","59","58","57","56",
                "55","53","52","51","50","49","48","47","46","45",
                "44","43","42","41","40"],"meta": {}})

    @mock.patch('httplib2.Http.request')
    def test_api_url_returns_200(self, mock_request):
        """Test for proxy URL returning something."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_resp
            ),
            r'/store/\d+/page/\d+/product/ids/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_ids
            ),
            r'/store/\d+/content/?\?tagged-products=\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({  # fake one-product response
                    'results': [json.loads(self.mock_resp)['results'][0]],
                    'meta': {}
                })
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
            r'store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_resp
            ),
            r'/store/\d+/page/\d+/product/ids/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_ids
            ),
            r'/store/\d+/content/?\?tagged-products=\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({  # fake one-product response
                    'results': [json.loads(self.mock_resp)['results'][0]],
                    'meta': {}
                })
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
    def test_api_url_has_products(self, mock_request):
        """Test for proxy URL returning valid json format."""

        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_resp
            ),
            r'/store/\d+/page/\d+/product/ids/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_ids
            ),
            r'/store/\d+/content/?\?tagged-products=\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({  # fake one-product response
                    'results': [json.loads(self.mock_resp)['results'][0]],
                    'meta': {}
                })
            ),
        })

        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        is_valid = len(json.loads(resp.content)['results']) > 0

        self.assertTrue(is_valid)
