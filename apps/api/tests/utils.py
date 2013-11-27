import re
from collections import namedtuple
from tastypie.test import ResourceTestCase

MockResponse = namedtuple('MockResponse', ['status_code', 'content', 'headers'])

def configure_mock_request(mock_request, returns):
    # http://www.voidspace.org.uk/python/mock/examples.html#multiple-calls-with-different-effects
    def response(uri, method='GET', body=None, headers=None):
        for key, value in returns.iteritems():
            if re.search(key, uri):
                return value

        RequestNotMocked = namedtuple('RequestNotMocked', 'status, response')
        return RequestNotMocked(None, None)

    # side_effect: A function to be called whenever the Mock is called
    mock_request.side_effect = response

    return mock_request

def configure_hammock_request(mock_request, returns):
    def response(method, url):
        for key, value in returns.iteritems():
            if re.search(key, url):
                resp = value[0]
                content = value[1]
                return MockResponse(
                    status_code=resp['status'],
                    content=content,
                    headers={}
                )

        RequestNotMocked = namedtuple('RequestNotMocked', 'status, response')
        return RequestNotMocked(None, None)

    # side_effect: A function to be called whenever the Mock is called
    mock_request.side_effect = response

    return mock_request


class AuthenticatedResourceTestCase(ResourceTestCase):
    """Logs in the proxy for subclassed test cases."""
    fixtures = ['users.json']

    def setUp(self):
        super(AuthenticatedResourceTestCase, self).setUp()

        # TODO: Make this a 'constant' somewhere relevant
        login_url = '/graph/v1/user/login/'
        login_credentials = {
            'username': 'test',
            'password': 'asdf'
        }

        self.api_client.post(
            login_url,
            data=login_credentials,
            format='json'
        )


