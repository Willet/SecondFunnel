"""The convenience api test case for our own tests"""


from tastypie.test import ResourceTestCase

import test_config as config


class ApiTestCase(ResourceTestCase):
    """Test runner needs to be "logged in"."""

    fixtures = ['dev_user_data.json', 'dev_store_data.json']

    def setUp(self):
        super(ApiTestCase, self).setUp()

        # self.api_url = config.base_url + '/store/38/product/live'
        self.headers = {'cache-control': 'no-cache',
                        'ApiKey': 'secretword',
                        'Content-type': 'application/json',
                        }

        self.api_client.post(config.login_url, data=config.valid_login)

    def tearDown(self):
        self.api_client.post(config.logout_url, data={})

        super(ApiTestCase, self).tearDown()

    def get_credentials(self):
        return self.create_basic(username=config.valid_login['username'],
                                 password=config.valid_login['password'])
