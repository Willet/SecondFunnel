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

        req_factory = RequestFactory()
        req = req_factory.get(self.api_url)
        req.user = User.objects.get(username='gap')

        self.mock_resp = json.loads(get_suggested_content_by_page(
            req, 38, 97).content)

    @mock.patch('httplib2.Http.request')
    def test_api_url_returns_200(self, mock_request):
        """Test for proxy URL returning something."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_resp
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
    def test_api_url_has_product_keys(self, mock_request):
        """Test for proxy URL returning valid json format."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                self.mock_resp
            ),
        })

        resp = self.api_client.get(self.api_url, format='json',
                                   authentication=self.get_credentials(),
                                   headers=self.headers)

        # "all keys are numeric, but are kept as strings because json"
        is_valid = all([str(int(x)) == x for x in \
                        json.loads(resp.content)['results'].keys()])

        self.assertTrue(is_valid)
