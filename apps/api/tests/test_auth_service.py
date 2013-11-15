from django.test import TestCase
from django.test import Client

# TODO fix (could not dump data)
# fixtures = ['api_tests.json']

# We will assume gap/gap is a valid user for now as I don't have fixtures yet
# TODO Replace when we have a fixture with test data
valid_login = {'username': 'gap', 'password': 'gap'}

base_url = '/graph/v1'
login_url = base_url + '/user/login'
logout_url = base_url + '/user/logout'
# TODO make sure this is actually a restricted URL
restricted_url = base_url + '/store'

def is_200(self, path):
    client = Client()
    response = client.get(path)
    return 200 == response.status_code

class LoginTest(TestCase):

    # Should return 401 if no credentials supplied
    def test_no_login_data(self):
        client = Client()
        response = client.post(login_url, {})
        self.assertEqual(response.status_code, 401, 'No login data (empty post) test failed')

    # Should return 401 if username does not exist
    def test_invalid_user(self):
        client = Client()
        response = client.post(login_url, valid_login)
        self.assertEqual(response.status_code, 401, 'Wrong username login test failed')

    # Should return 401 if password does not exist
    def test_invalid_password(self):
        client = Client()
        response = client.post(login_url, {'username': 'fake', 'password': 'I swear'})
        self.assertEqual(401, response.status_code, 'Invalid password test failed')

    # Should return 200 if valid credentials
    # TODO figure out this mocking situation
    def test_valid_credentials(self):
        client = Client()
        response = client.post(login_url, {'username': self.username, 'password': self.password})
        self.assertEqual(response.status_code, 200, 'Valid credentials did not work')
        # Now you should be able to access stuff but that's not a unit test


    # Should revoke existing credentials if invalid credentials supplied

class LogoutTest(TestCase):
    # Should return 200 if logged in
    def test_logged_in(self):
        # TODO skip if login test fails because logout is useless without login
        # self.skipTest('Login failed')
        client = Client()
        response = client.post(login_url, valid_login)
        response = client.post(logout_url)
        self.assertEqual(200, response.status_code, 'Logout did not return 200 when we were logged in')



    # Should return 200 if logged out
    def test_logged_out(self):
        client = Client()
        response = client.post(logout_url)
        self.assertEqual(response.status_code, 200, 'Logout did not return 200 when we were logged out')



    # Should revoke credentials
    def test_revokes_credentials(self):
        # TODO skip if login test fails because logout is useless without login
        # self.skipTest('Login failed')

        client = Client()
        response = client.post(login_url, valid_login)

        # Assume login worked because test would have been skipped

        #This is probably unnecessary because we check above
        #TODO make sure response keeps cookies
        response = client.post(logout_url)
        self.assertEqual(200, response.status_code, 'Revoking credentials did not work (status code' +
                                                    response.status_code + ')')

        self.assertEqual(401, response.status_code, 'Revoking credentials did not work')


