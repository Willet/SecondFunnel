from tastypie.test import TestApiClient, ResourceTestCase
from .test_config import *
import mock
import re
import json

class ProxyTest(ResourceTestCase):
    fixtures = default_fixtures

    # Should return 200 if valid credentials
    @mock.patch('httplib2.Http.request')
    def test_valid_request(self, mock_request):
        configure_mock_request(mock_request,{
            re.compile(proxy_url): (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps(mocks.store_list)
            )

        })
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.get(append_slash(proxy_url))
        self.assertHttpOK(response)

    # should return 401 if invalid credentials
    @mock.patch('httplib2.Http.request')
    def test_unauthorized(self, mock_request):
        configure_mock_request(mock_request,{
            re.compile(append_slash(restricted_url)): (
                {'status': 401, 'content-type': 'application/json'},
                json.dumps(mocks.store_list)
            )

        })
        client = TestApiClient()
        response = client.get(append_slash(restricted_url))
        self.assertHttpUnauthorized(response)

    # should return 404 if authorized and resource DNE
    @mock.patch('httplib2.Http.request')
    def test_nonexistent_content(self, mock_request):
        nonexistent_path = '/I don not exist'
        request_url = base_url + nonexistent_path
        configure_mock_request(mock_request,{
            re.compile(CONTENTGRAPH_BASE_URL + nonexistent_path): (
                {'status': 404, 'content-type': 'application/json'},
                json.dumps(mocks.store_list)
            )
        })
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.get(request_url)
        self.assertHttpNotFound(response)

    # should return 401 if unauthorized and content DNE
    @mock.patch('httplib2.Http.request')
    def test_unauthorized_nonexistent_content(self, mock_request):
        request_url = restricted_url + '/I do not exist'
        configure_mock_request(mock_request,{
            re.compile(request_url): (
                {'status': 401, 'content-type': 'application/json'},
                json.dumps(mocks.store_list)
            )
        })
        client = TestApiClient()
        response = client.get(request_url)
        self.assertHttpUnauthorized(response)

    # Should return resource if resource exists
    @mock.patch('httplib2.Http.request')
    def test_fetch_resource(self, mock_request, client=logged_in_client()):
        configure_mock_request(mock_request,{
            re.compile(CONTENTGRAPH_BASE_URL + restricted_path): (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps(mocks.store_list)
            )

        })
        response = client.get(restricted_url)
        # TODO expect actual resource
        self.assertHttpOK(response)
        self.assertEqual(mocks.store_list, json.loads(response.content), 'Proxy did not send the content we asked for')
