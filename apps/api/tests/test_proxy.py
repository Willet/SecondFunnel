from django.test import TestCase
from django.test import Client

class proxyTest(TestCase):

    # Should return 200 if valid credentials

    # should return 401 if invalid credentials
    def test_unauthorized(self):
        client = Client()
        response = client.get('/proxy')

    # should return 404 if authorized and resource DNE

    # Should return resource if resource exists
