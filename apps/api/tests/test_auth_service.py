from tastypie.test import TestApiClient, ResourceTestCase
from .test_config import *
from json import loads as read_json
import mock

# TODO Once we figure out how we should handle the following, we need to add tests
# - users can only access their content, not everybody's
# -

class LoginTest(ResourceTestCase):
    fixtures = default_fixtures

    # Should return 401 if no credentials supplied
    def test_no_login_data(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data={})
        self.assertHttpUnauthorized(response)

    # Should return 401 if username does not exist
    def test_invalid_user(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data={'username': 'fake', 'password': 'I swear'})
        self.assertHttpUnauthorized(response)

    # Should return 401 if password does not exist
    def test_invalid_password(self):
        client = TestApiClient()
        response = client.post(login_url,format='json', data={'username': 'gap', 'password': 'not the right pw'})
        self.assertHttpUnauthorized(response)

    # Should return 200 if valid credentials
    def test_valid_credentials(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        self.assertHttpOK(response)

    # I'm not sure where this should go but initially this is a good place for it to sit
    # Should give you access to restricted areas if you're logged in
    def test_access_after_login(self):
        client = TestApiClient()
        client.post(login_url, format='json', data=valid_login)
        response = client.get(append_slash(restricted_url))
        self.assertHttpOK(response)

    # Should revoke existing credentials if invalid credentials supplied
    def test_revokes_on_invalid(self):
        client = TestApiClient()
        client.post(login_url, format='json', data=valid_login)
        client.post(login_url, format='json', data={'username': 'fake', 'password': 'fake'})
        response = client.get(restricted_url)
        self.assertHttpUnauthorized(response)


    def test_sends_json(self):
        '''Test that we receive a JSON object
        '''
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        decoded_json = None
        valid_json = True # innocent until proven guilty

        try:
            global decoded_json
            decoded_json = read_json(response.content)
        except:
            valid_json = False

        self.assertTrue(valid_json,'Login did not return a valid JSON object')

    def test_sends_user_data(self):
        '''Test that what we receive contains the actual user data
        '''
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        decoded_json = None
        valid_json = True

        try:
            global decoded_json
            decoded_json = read_json(response.content)
        except:
            valid_json = False

        self.assertEqual(valid_login['username'], decoded_json['username'])


class LogoutTest(ResourceTestCase):
    fixtures = default_fixtures

    # Should return 200 if logged in
    def test_logged_in(self):
        client = TestApiClient()
        client.post(login_url, format='json', data=valid_login)
        response = client.post(logout_url)
        self.assertHttpOK(response)

    # Should return 200 if logged out
    def test_logged_out(self):
        client = TestApiClient()
        response = client.post(logout_url)
        self.assertHttpOK(response)

    # Should revoke credentials
    def test_revokes_credentials(self):
        client = TestApiClient()
        client.post(login_url,format='json', data=valid_login)
        response = client.post(append_slash(restricted_url))
        self.assertHttpUnauthorized(response)
