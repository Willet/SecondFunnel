from django.test import TestCase
from tastypie.test import TestApiClient
from .test_config import *

class ProxyTest(TestCase):
    # TODO skip if login test fails

    # Should return 200 if valid credentials
    def test_valid_request(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)

        response = client.get(restricted_url)
        self.assertEqual(200, restricted_url)

    # should return 401 if invalid credentials
    def test_unauthorized(self):
        client = TestApiClient()
        response = client.get(proxy_url + '/store/38')
        self.assertEqual(401, response.status_code, 'Proxy did not return 401 to unauthorized request')

    # should return 404 if authorized and resource DNE

    # Should return resource if resource exists
