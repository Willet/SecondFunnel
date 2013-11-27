import json
from tastypie.test import ResourceTestCase


class UserLoginTestSuite(ResourceTestCase):
    fixtures = ['users.json']

    def test_no_login_data(self):
        response = self.api_client.post(
            '/graph/v1/user/login',
            format='json',
            data={}
        )
        self.assertHttpUnauthorized(response)

    def test_invalid_username(self):
        response = self.api_client.post(
            '/graph/v1/user/login',
            format='json',
            data={
                'username': 'banana',
                'password': 'banana'
            }
        )
        self.assertHttpUnauthorized(response)

    def test_invalid_password(self):
        response = self.api_client.post(
            '/graph/v1/user/login',
            format='json',
            data={
                'username': 'test',
                'password': 'banana'
            }
        )
        self.assertHttpUnauthorized(response)

    def test_valid_login(self):
        response = self.api_client.post(
            '/graph/v1/user/login',
            format='json',
            data={
                'username': 'test',
                'password': 'asdf'
            }
        )
        self.assertHttpOK(response)

        expected = {
            "is_active": True,
            "stores": [],
            "username": "test"
        }
        user = json.loads(response.content)

        self.assertDictContainsSubset(
            expected,
            user
        )

        response = self.api_client.get(
            '/graph/v1/user/1/',
            format='json'
        )
        self.assertHttpOK(response)

    # TODO: It appears that this test should have failed originally,
    # but doesn't
    def xtest_credentials_revocation(self):
        response = self.api_client.post(
            '/graph/v1/user/login',
            format='json',
            data={
                'username': 'test',
                'password': 'asdf'
            }
        )

        self.assertHttpOK(response)
        response = self.api_client.post(
            '/graph/v1/user/login',
            format='json',
            data={
                'username': 'test',
                'password': 'banana'
            }
        )
        self.assertHttpUnauthorized(response)

        response = self.api_client.get(
            '/graph/v1/user/1/',
            format='json'
        )
        self.assertHttpUnauthorized(response)

class UserLogoutTestSuite(ResourceTestCase):
    fixtures = ['users.json']

    def test_logged_in(self):
        response = self.api_client.post(
            '/graph/v1/user/login',
            format='json',
            data={
                'username': 'test',
                'password': 'asdf'
            }
        )
        self.assertHttpOK(response)

        response = self.api_client.post(
            '/graph/v1/user/logout',
            format='json'
        )
        self.assertHttpOK(response)

    def test_logged_out(self):
        response = self.api_client.post(
            '/graph/v1/user/logout',
            format='json'
        )
        self.assertHttpUnauthorized(response)


