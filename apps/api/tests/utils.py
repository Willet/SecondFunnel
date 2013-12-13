import json
import mock
import random
import re
import requests
import string
from collections import namedtuple
from tastypie.test import ResourceTestCase, TestApiClient

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
    def response(method, url, **kwargs):
        for key, value in returns.iteritems():
            if re.search(key, url):
                resp = value[0]
                content = value[1]
                return MockResponse(
                    status_code=resp['status'],
                    content=content,
                    headers=resp
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

class MockedHammockRequestsTestCase(AuthenticatedResourceTestCase):
    '''Mocks out requests.Session.request with a mock request. The mock request
    has some default return values, these can be over-written by calling tests.
    For consecutive calls you can override the mock_*_list properties.
    '''
    def setUp(self):
        super(MockedHammockRequestsTestCase, self).setUp()

        self.mock_content_default = {
            'test': 'data',
            'random': ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32)) #TODO make a random string
        }
        self.mock_content_list = []

        self.mock_status_default = 200
        self.mock_status_list = []

        inject_variables = {
            'calls': 0
        }
        def side_effect(*args, **kwargs):
            calls = inject_variables['calls']
            mock_status = self.mock_status_default
            if len(self.mock_status_list) > calls:
                mock_status = self.mock_status_list[calls]

            mock_content = self.mock_content_default
            if len(self.mock_content_list) > calls:
                mock_content = self.mock_status_list[calls]

            inject_variables['calls'] += 1
            return MockResponse(
                status_code=mock_status,
                content=json.dumps(mock_content),
                headers={'content-type': 'application/json'}
            )

        self.mock_request = mock.Mock(side_effect=side_effect)
        self.mocks = mock.patch.object(requests.Session, 'request', self.mock_request)
        self.mocks.start()
        self.addCleanup(self.mocks.stop)

class BaseNotAuthenticatedTests(object):
    """Test method assumes that the subclass will have the following properties
          self.url - String url to be called
          self.mock_request - Mock() instance
          self.allowed_methods - list of methods that will 200 under normal circumstances
                                 must be of length > 0
    """
    def test_not_authenticated(self):
        client = TestApiClient()
        response = getattr(client, self.allowed_methods[0])(self.url, format='json', data={})

        self.assertFalse(self.mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(self.mock_request.call_count, 0)

        self.assertHttpUnauthorized(response)
        self.assertEqual(response._headers['content-type'][1], 'application/json')
        self.assertEqual(json.dumps({
            'error': 'Not logged in'
        }), response.content)

class BaseMethodNotAllowedTests(object):
    """Test method assumes that the subclass will have the following properties
          self.url - String url to be called
          self.mock_request - Mock() instance
          self.allowed_methods - list of methods that will 200 under normal circumstances
    """
    def test_bad_method(self):
        verbs = {
            'get': None,
            'post': {},
            'put': {},
            'patch': {},
            'delete': None
        }

        for verb in verbs:
            if verb in self.allowed_methods:
                continue

            response = getattr(self.api_client, verb)(self.url, format='json', data=verbs[verb])
            self.assertFalse(self.mock_request.called, 'Mock request was still called when bad method was used')
            self.assertEqual(self.mock_request.call_count, 0)
            self.assertHttpMethodNotAllowed(response)
