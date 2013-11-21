from django.test import TestCase
from tastypie.test import TestApiClient
from .test_config import *

class ProxyTest(TestCase):
    fixtures = default_fixtures

    # Should return 200 if valid credentials
    def test_valid_request(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.get(slashed(proxy_url))
        self.assertEqual(200, response.status_code, 'Proxy did not return 200 after we logged in')

    # should return 401 if invalid credentials
    def test_unauthorized(self):
        client = TestApiClient()
        response = client.get(slashed(restricted_url))
        self.assertEqual(401, response.status_code, 'Proxy did not return 401 to unauthorized request')

    # should return 404 if authorized and resource DNE
    def test_nonexistent_content(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.get(restricted_url + '/I do not exist')
        self.assertEqual(404, response.status_code, 'Proxy did not return 404 on nonexistent content')

    # Should return resource if resource exists
    def test_fetch_resource(self):
        client = LoggedInClient()
        response = client.get(resource_url)
        # TODO expect actual resource
        self.assertEqual(200, response.status_code, 'Proxy did not return 200 on valid content')
        # self.assertEqual(resource.data, response.content, 'Proxy did not return the content we asked for')
