import re

from collections import namedtuple

from tastypie.test import ResourceTestCase

from apps.api.tests import test_config as config


def configure_mock_request(mock_request, returns):
    # http://www.voidspace.org.uk/python/mock/examples.html#multiple-calls-with-different-effects
    def response(url, method='GET', body=None, headers=None):
        for key, value in returns.iteritems():
            if re.search(key, url):
                return value

        RequestNotMocked = namedtuple('RequestNotMocked', 'status, response')
        return RequestNotMocked(None, None)

    # side_effect: A function to be called whenever the Mock is called
    mock_request.side_effect = response

    return mock_request


class AuthenticatedTestCase(ResourceTestCase):
    """Logs in the proxy for subclassed test cases."""
    fixtures = ['dev_user_data.json', 'dev_store_data.json']

    def setUp(self):
        super(AuthenticatedTestCase, self).setUp()

        # self.api_url = config.base_url + '/store/38/product/live'
        self.headers = {'cache-control': 'no-cache',
                        'ApiKey': 'secretword',
                        'Content-type': 'application/json',
                        }

        self.api_client.post(config.login_url, data=config.valid_login)

    def tearDown(self):
        self.api_client.post(config.logout_url, data={})

        super(AuthenticatedTestCase, self).tearDown()

    def get_credentials(self):
        return self.create_basic(username=config.valid_login['username'],
                                 password=config.valid_login['password'])
