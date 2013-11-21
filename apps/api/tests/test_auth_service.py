from django.test import TestCase
from tastypie.test import TestApiClient
from .test_config import *
from json import loads as read_json

# TODO Once we figure out how we should handle the following, we need to add tests
# - users can only access their content, not everybody's
# -

class LoginTest(TestCase):
    fixtures = default_fixtures

    # Should return 401 if no credentials supplied
    def test_no_login_data(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data={})
        self.assertEqual(response.status_code, 401, 'No login data (empty post) test failed')

    # Should return 401 if username does not exist
    def test_invalid_user(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data={'username': 'fake', 'password': 'I swear'})
        self.assertEqual(response.status_code, 401, 'Wrong username login test failed')

    # Should return 401 if password does not exist
    def test_invalid_password(self):
        client = TestApiClient()
        response = client.post(login_url,format='json', data={'username': 'gap', 'password': 'not the right pw'})
        self.assertEqual(401, response.status_code, 'Invalid password test failed')

    # Should return 200 if valid credentials
    # TODO figure out this mocking situation
    def test_valid_credentials(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        self.assertEqual(200, response.status_code, 'Did not receive 200 on valid credentials')

    # I'm not sure where this should go but initially this is a good place for it to sit
    # Should give you access to restricted areas if you're logged in
    def test_access_after_login(self):
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        response = client.get(slashed(restricted_url))
        self.assertEqual(200, response.status_code, 'We don\'t have access to resources after login')

    # Should revoke existing credentials if invalid credentials supplied
    def test_revokes_on_invalid(self):
        client = TestApiClient()
        response = client.post(login_url,format='json', data=valid_login)

    def test_sends_json(self):
        '''
        Test that we receive a JSON object
        '''
        client = TestApiClient()
        response = client.post(login_url, format='json', data=valid_login)
        decoded_json = False
        valid_json = True

        # TODO is there a better way
        try:
            global decoded_json
            decoded_json = read_json(response.content)
        except:
            valid_json = False

        self.assertTrue(valid_json,'Login did not return a valid JSON object')

    def test_sends_user_data(self):
        '''
        Test that what we receive contains the actual user data
        '''

class LogoutTest(TestCase):
    fixtures = default_fixtures

    # Should return 200 if logged in
    def test_logged_in(self):
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
        response = client.post(slashed(restricted_url))
        self.assertEqual(401, response.status_code, 'Revoking credentials did not work')
