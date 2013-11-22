from django.test import TestCase
from tastypie.test import TestApiClient
from .test_config import *
import mock
import re
import json

class ProxyTest(TestCase):
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
        self.assertEqual(200, response.status_code, 'Proxy did not return 200 after we logged in')

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
        self.assertEqual(401, response.status_code, 'Proxy did not return 401 to unauthorized request')

    # should return 404 if authorized and resource DNE
    @mock.patch('httplib2.Http.request')
    def test_nonexistent_content(self, mock_request):
        request_url = restricted_url + '/I do not exist'
        configure_mock_request(mock_request,{
            re.compile(request_url): (
                {'status': 404, 'content-type': 'application/json'},
                json.dumps(mocks.store_list)
            )
        })
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.get(request_url)
        self.assertEqual(404, response.status_code, 'Proxy did not return 404 on nonexistent content')

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
        self.assertEqual(401, response.status_code, 'Proxy did not return 401 on (unauthorized + not found)')

    # Should return resource if resource exists
    @mock.patch('httplib2.Http.request')
    def test_fetch_resource(self, mock_request):
        configure_mock_request(mock_request,{
            re.compile(restricted_url): (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps(mocks.store_list)
            )

        })
        client = LoggedInClient()
        response = client.get(restricted_url)
        # TODO expect actual resource
        self.assertEqual(200, response.status_code, 'Proxy did not return 200 on valid content')
        self.assertEqual(mocks.page, json.loads(response.content), 'Proxy did not return the content we asked for')
