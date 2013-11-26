import json
import mock
import requests
from tastypie.test import ResourceTestCase
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request, configure_hammock_request


class UnauthenticatedContentTestSuite(ResourceTestCase):
    def test_unauthorized(self):
        response = self.api_client.get(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)

# TODO: How can we better name these test methods?
# TODO: Should we have separate test folders for different cases instead?
# TODO: Move mock_request dictionaries somewhere else.
class AuthenticatedContentTestSuite(AuthenticatedResourceTestCase):
    @mock.patch('httplib2.Http.request')
    def test_add_content_success(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        # TODO: Make URL pattern a 'constant' in somewhere relevant
        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_add_content_proxy_add_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

    @mock.patch('httplib2.Http.request')
    def test_add_content_tileconfig_add_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

    @mock.patch('httplib2.Http.request')
    def test_remove_content_success(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.delete(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_remove_content_proxy_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.delete(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

    @mock.patch('httplib2.Http.request')
    def test_remove_content_tile_config_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.delete(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

    @mock.patch('httplib2.Http.request')
    def test_get_all_content(self, mock_request):
        """tests the response when attempting to retrieve all content
        from a page.

        """
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.get('/graph/v1/store/1/page/1/content',
            format='json')

        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_get_single_content(self, mock_request):
        """tests the response when attempting to retrieve all content
        from a page.

        """
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'store/\d+/content/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.get('/graph/v1/store/1/page/1/content',
            format='json')
        self.assertHttpOK(response)

        response = self.api_client.get('/graph/v1/store/1/content/915',
            format='json')
        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_get_by_product_id(self, mock_request):
        """Test for proxy URL returning something."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'/store/\d+/page/\d+/product/ids/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({"results": ["65", "64", "63"], "meta": {}})
            ),
            r'/store/\d+/content/?\?tagged-products=\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({"results": [], "meta": {}})
            ),
        })

        response = self.api_client.get(
            '/graph/v1/store/38/page/97/content/suggested',
            format='json'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)
        # TODO: Verify that data is correct?
        # Previously: is_valid = len(json.loads(resp.content)['results']) > 0

    @mock.patch.object(requests.Session, 'request')
    def test_valid_rejections(self, mock_request):
        mock_request = configure_hammock_request(mock_request, {
            r'store/\d+/content/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.post(
            '/graph/v1/store/38/content/1077/reject',
            data={}
        )
        self.assertHttpOK(response)

    @mock.patch.object(requests.Session, 'request')
    def test_invalid_rejections(self, mock_request):
        mock_request = configure_hammock_request(mock_request, {
            r'store/\d+/content/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.get(
            '/graph/v1/store/38/content/1077/reject',
            data={}
        )
        self.assertHttpMethodNotAllowed(response)
        # If we want, we can verify JSON response as well

        response = self.api_client.patch(
            '/graph/v1/store/38/content/1077/reject',
            data={}
        )
        self.assertHttpMethodNotAllowed(response)