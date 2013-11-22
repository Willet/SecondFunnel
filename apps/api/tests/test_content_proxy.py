import json
import re
import mock
from tastypie.test import ResourceTestCase
from apps.api.tests.utils import configure_mock_request


class UnauthenticatedContentProxyTest(ResourceTestCase):
    def setUp(self):
        super(UnauthenticatedContentProxyTest, self).setUp()

    def tearDown(self):
        pass

    def test_unauthorized(self):
        response = self.api_client.get(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)


class ContentProxyTest(ResourceTestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(ContentProxyTest, self).setUp()

        # Presently, doesn't appear to be any create_session_authentication
        # method... so, need to login manually
        response = self.api_client.post(
            '/graph/v1/user/login/',
            format='json',
            data={
                'username': 'test',
                'password': 'asdf'
            }
        )

    def tearDown(self):
        self.api_client.post(
            '/graph/v1/user/logout/',
            format='json'
        )

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