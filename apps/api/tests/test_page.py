import json
import mock
import requests
import random
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request, configure_hammock_request
from collections import namedtuple
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

        #Seting up mocks
        self.MockResponse = namedtuple('MockResponse', ['status_code', 'content', 'headers'])
        def side_effect(*args, **kwargs):
            return self.MockResponse(status_code=200, content='', headers={})
        
        self.mock_request = mock.Mock(side_effect=side_effect)
        self.mocks = mock.patch.object(requests.Session, 'request', self.mock_request)
        self.mocks.start()
        self.addCleanup(self.mocks.stop)

    def test_all_good(self):
        response = self.api_client.put(self.url, format='json', data=self.content_data)
        self.assertTrue(self.mock_request.called, 'Mock request was never made')
        self.assertEqual(self.mock_request.call_count, len(self.content_data), 'Mock was not called the correct number of times')
        
        for i in range(len(self.content_data)):
            self.assertEqual(self.mock_request.call_args_list[i][0], 
                ('put', settings.CONTENTGRAPH_BASE_URL + '/store/%s/page/%s/content/%s' % (self.store_id, self.page_id, self.content_data[i])))

        self.assertHttpOK(response)

    def test_not_authenticated(self):
        client = TestApiClient()
        response = client.put(self.url, format='json', data=self.content_data)

        self.assertFalse(self.mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(self.mock_request.call_count, 0)

        self.assertHttpUnauthorized(response)
        self.assertEqual(response._headers['content-type'][1], 'application/json')
        self.assertEqual(json.dumps({
            'error': 'Not logged in'
        }), response.content)

    def test_bad_request_method(self):
        verbs = [
            {
                'verb': 'get'
            },
            {
                'verb': 'post',
                'data': True
            },
            {
                'verb': 'patch',
                'data': True
            },
            {
                'verb': 'delete'
            }
        ]

        for verb in verbs:
            data = None
            if 'data' in verb:
                data = self.content_data
            
            response = getattr(self.api_client, verb['verb'])(self.url, format='json', data=data)
            self.assertFalse(self.mock_request.called, 'Mock request was still called when user was not logged in')
            self.assertEqual(self.mock_request.call_count, 0)
            self.assertHttpMethodNotAllowed(response)

    def test_bad_json(self):
        response = self.api_client.put(self.url, format='json', data={
            "abc": "def"
        })
        self.assertFalse(self.mock_request.called, 'Mock request was still called when bad json data was provided')
        self.assertHttpApplicationError(response)

        response = self.api_client.put(self.url, format='xml', data='&$dsadsad""rfwefsf{}[]dffds')
        self.assertFalse(self.mock_request.called, 'Mock request was still called when bad json data was provided')
        self.assertHttpApplicationError(response)

        response = self.api_client.put(self.url, format='json', data=[
            {
                "abc": "def"
            },
            {
                "ghi": "jkl"
            }
        ])
        self.assertFalse(self.mock_request.called, 'Mock request was still called when bad json data was provided')
        self.assertHttpApplicationError(response)

    def test_remote_errors(self):
        inject_variables = {
            'calls': 0
        }

        def side_effect(*args, **kwargs):
            if inject_variables['calls'] == 0:
                inject_variables['calls'] += 1
                return self.MockResponse(status_code = 200, content = '', headers = {})
            elif inject_variables['calls'] == 1:
                inject_variables['calls'] += 1
                return self.MockResponse(status_code = 500, content = '', headers = {})
            elif inject_variables['calls'] == 2:
                self.fail('Mock called too many times')
        
        self.mock_request.side_effect = side_effect

        response = self.api_client.put(self.url, format='json', data=self.content_data)
        self.assertTrue(self.mock_request.called, 'Mock request was never made')
        self.assertEqual(self.mock_request.call_count, 2, 'Mock was not called the correct number of times')
        self.assertEqual(self.mock_request.call_args_list[0][0], 
                ('put', settings.CONTENTGRAPH_BASE_URL + '/store/%s/page/%s/content/%s' % (self.store_id, self.page_id, self.content_data[0])))
        self.assertEqual(self.mock_request.call_args_list[1][0], 
                ('put', settings.CONTENTGRAPH_BASE_URL + '/store/%s/page/%s/content/%s' % (self.store_id, self.page_id, self.content_data[1])))
        self.assertHttpApplicationError(response)
