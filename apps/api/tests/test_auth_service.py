from django.test import TestCase
from tastypie.test import TestApiClient
from .test_config import *


def is_200(self, path):
    client = TestApiClient()
    response = client.get(path)
    return 200 == response.status_code

class LoginTest(TestCase):

    # Should return 401 if no credentials supplied
    def test_no_login_data(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data={})
        self.assertEqual(response.status_code, 401, 'No login data (empty post) test failed')

    # Should return 401 if username does not exist
    def test_invalid_user(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        self.assertEqual(response.status_code, 401, 'Wrong username login test failed')

    # Should return 401 if password does not exist
    def test_invalid_password(self):
        client = TestApiClient()
        response = client.post(login_url,format='json', data={'username': 'fake', 'password': 'I swear'})
        self.assertEqual(401, response.status_code, 'Invalid password test failed')

    # Should return 200 if valid credentials
    # TODO figure out this mocking situation
    def test_valid_credentials(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        self.assertEqual(response.status_code, 200, 'Valid credentials did not work')

    # I'm not sure where this should go but initially this is a good place for it to sit
    # Should give you access to restricted areas if you're logged in
    def test_access_after_login(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.get(restricted_url)
        self.assertEqual(200, response.status_code, 'We don\'t have access to resources after login')

    # Should revoke existing credentials if invalid credentials supplied
    def test_revokes_on_invalid(self):
        client = TestApiClient()
        response = client.post(login_url,format='json', data=valid_login)


class LogoutTest(TestCase):
    # Should return 200 if logged in
    def test_logged_in(self):
        # TODO skip if login test fails because logout is useless without login
        # self.skipTest('Login failed')
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.post(logout_url)
        self.assertEqual(200, response.status_code, 'Logout did not return 200 when we were logged in')

    # Should return 200 if logged out
    def test_logged_out(self):
        client = TestApiClient()
        response = client.post(logout_url)
        self.assertEqual(response.status_code, 200, 'Logout did not return 200 when we were logged out')

    # Should revoke credentials
    def test_revokes_credentials(self):

        client = TestApiClient()
        response = client.post(login_url,format='json', data=valid_login)

        response = client.post(restricted_url)

        self.assertEqual(401, response.status_code, 'Revoking credentials did not work')


