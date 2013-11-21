import json
import re
import mock
from tastypie.test import ResourceTestCase


class UnauthenticatedContentProxyTest(ResourceTestCase):
    def setUp(self):
        super(UnauthenticatedContentProxyTest, self).setUp()

    def tearDown(self):
        pass

    def test_unauthorized(self):
        response = self.api_client.get(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)


class ContentProxyTest(ResourceTestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(ContentProxyTest, self).setUp()

        # Presently, doesn't appear to be any create_session_authentication
        # method... so, need to login manually
        response = self.api_client.post(
            '/graph/v1/user/login/',
            format='json',
            data={
                'username': 'test',
                'password': 'asdf'
            }
        )

    def tearDown(self):
        # TODO: Why is trailing slash required?
        self.api_client.post(
            '/graph/v1/user/logout/',
            format='json'
        )

    #@mock.patch('httplib2.Response')
    @mock.patch('httplib2.Http.request')
    def test_regular_success(self, mock_request):
        returns = {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        }

        # http://www.voidspace.org.uk/python/mock/examples.html#multiple-calls-with-different-effects
        def response(url, method, body, headers):
            # Pick the right response to return
            for key, value in returns.iteritems():
                if re.search(key, url):
                    return value

            # return some default?
            # fail test case?
            return (None, None)

        mock_request.side_effect = response

        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpOK(response)