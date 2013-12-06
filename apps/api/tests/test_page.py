import json
import mock
import requests
import random
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request, configure_hammock_request
from django.conf import settings
from tastypie.test import TestApiClient

class AuthenticatedPageTestSuite(AuthenticatedResourceTestCase):

    @mock.patch('httplib2.Http.request')
    def test_add_tile(self, mock_request):
        """checks if the proxy handles all mocked tile calls."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/\w+/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': {  # fake tile
                        'id': 1
                    }
                })
            ),
            r'page/\d+/tile/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': []
                })
            ),
        })

        # handles product
        response = self.api_client.put(
            '/graph/v1/store/1/page/1/product/1',
            format='json'
        )
        self.assertHttpOK(response)

        # handles content
        response = self.api_client.put(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpOK(response)

        # hits /tile-config
        response = self.api_client.put(
            '/graph/v1/page/1/tile-config',
            format='json'
        )
        self.assertHttpOK(response)

        # hits /tile
        response = self.api_client.put(
            '/graph/v1/page/1/tile',
            format='json'
        )
        self.assertHttpOK(response)

class AuthenticatedPageAddAllContentTests(AuthenticatedResourceTestCase):
    def setUp(self):
        super(AuthenticatedPageAddAllContentTests, self).setUp()
        self.store_id = 1
        self.page_id = 1
        self.content_data = [15, 12, random.randint(16, 1000)]
        self.mock_url_pattern = r'store/\d+/page/\d+/content/\d+/?'
        self.url = '/graph/v1/store/%s/page/%s/content/add_all' % (self.store_id, self.page_id)

    @mock.patch.object(requests.Session, 'request')
    def test_all_good(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            self.mock_url_pattern: (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.put(self.url, format='json', data=self.content_data)
        
        self.assertTrue(mock_request.called, 'Mock request was never made')
        self.assertEqual(mock_request.call_count, len(self.content_data), 'Mock was not called the correct number of times')
        
        for i in range(len(self.content_data)):
            self.assertEqual(mock_request.call_args_list[i][0], 
                ('put', settings.CONTENTGRAPH_BASE_URL + '/store/%s/page/%s/content/%s' % (self.store_id, self.page_id, self.content_data[i])))

        self.assertHttpOK(response)

    @mock.patch.object(requests.Session, 'request')
    def test_not_authenticated(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            self.mock_url_pattern: (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })        

        client = TestApiClient()
        response = client.put(self.url, format='json', data=self.content_data)

        self.assertFalse(mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(mock_request.call_count, 0)

        self.assertHttpUnauthorized(response)
        self.assertEqual(response._headers['content-type'][1], 'application/json')
        self.assertEqual(json.dumps({
            'error': 'Not logged in'
        }), response.content)

    @mock.patch.object(requests.Session, 'request')
    def test_bad_request_method(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            self.mock_url_pattern: (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.get(self.url, format='json')
        self.assertFalse(mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(mock_request.call_count, 0)
        self.assertHttpMethodNotAllowed(response)

        response = self.api_client.post(self.url, format='json', data=self.content_data)
        self.assertFalse(mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(mock_request.call_count, 0)
        self.assertHttpMethodNotAllowed(response)

        response = self.api_client.patch(self.url, format='json', data=self.content_data)
        self.assertFalse(mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(mock_request.call_count, 0)
        self.assertHttpMethodNotAllowed(response)

        response = self.api_client.delete(self.url, format='json')
        self.assertFalse(mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(mock_request.call_count, 0)
        self.assertHttpMethodNotAllowed(response)

    @mock.patch.object(requests.Session, 'request')
    def test_bad_json(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            self.mock_url_pattern: (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.put(self.url, format='json', data=json.dumps({
            "abc": "def"
        }))

        self.assertFalse(mock_request.called, 'Mock request was still called when bad json data was provided')
        self.assertHttpApplicationError(response)

        response = self.api_client.put(self.url, format='xml', data='&$dsadsad""rfwefsf{}[]dffds')

        self.assertFalse(mock_request.called, 'Mock request was still called when bad json data was provided')
        self.assertHttpApplicationError(response)

        response = self.api_client.put(self.url, format='json', data=json.dumps([
            {
                "abc": "def"
            },
            {
                "ghi": "jkl"
            }
        ]))

        #TODO: This should fail with the current implementation, but for some reason the decoded json type
        #      resolves as type 'unicode' instead of type 'list' which gets caught by the code to handle
        #      the first request in this test case
        self.assertFalse(mock_request.called, 'Mock request was still called when bad json data was provided')
        self.assertHttpApplicationError(response)
        self.fail()

    @mock.patch.object(requests.Session, 'request')
    def test_remote_errors(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            self.mock_url_pattern: (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        #TODO