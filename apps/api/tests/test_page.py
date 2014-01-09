import json
import mock
import random
import requests
from apps.api.tests.utils import BaseMethodNotAllowedTests
from collections import namedtuple

from django.conf import settings
from tastypie.test import TestApiClient

from apps.api.tests.utils import (AuthenticatedResourceTestCase,
                                  configure_mock_request,
                                  MockedHammockRequestsTestCase,
                                  BaseNotAuthenticatedTests)


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

class AuthenticatedPageAddAllContentTests(MockedHammockRequestsTestCase, BaseNotAuthenticatedTests, BaseMethodNotAllowedTests):
    def setUp(self):
        super(AuthenticatedPageAddAllContentTests, self).setUp()
        self.page_id = 1
        self.content_data = [15, 12, random.randint(16, 1000)]
        self.url = '/graph/v1/store/1/page/%s/content/add_all' % (self.page_id)
        self.allowed_methods = ['put']

        self.mock_content_default = {
            'results': []
        }

        self.mock_content_list = [
            self.mock_content_default,
            self.mock_content_default,
            {
                'results': [
                    {
                        'template': 'image',
                        'content-ids': [12]
                    }
                ]
            }
        ]

    def test_all_good(self):
        response = self.api_client.put(self.url, format='json', data=self.content_data)
        self.assertTrue(self.mock_request.called, 'Mock request was never made')
        expected_mock_calls = 5
        self.assertEqual(self.mock_request.call_count, expected_mock_calls, 'Mock was not called the correct number of times; Was: %s, Expected: %s' % (self.mock_request.call_count, expected_mock_calls))
        
        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': self.content_data[0],
                'template': 'image'
            }
        })
        args, kwargs = self.mock_request.call_args_list[1]
        self.assertEqual(args, ('post', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'data': json.dumps({
                'content-ids': [self.content_data[0]],
                'template': 'image',
                'prioritized': False
            })
        })

        args, kwargs = self.mock_request.call_args_list[2]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': self.content_data[1],
                'template': 'image'
            }
        })

        args, kwargs = self.mock_request.call_args_list[3]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': self.content_data[2],
                'template': 'image'
            }
        })
        args, kwargs = self.mock_request.call_args_list[4]
        self.assertEqual(args, ('post', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'data': json.dumps({
                'content-ids': [self.content_data[2]],
                'template': 'image',
                'prioritized': False
            })
        })

        self.assertHttpOK(response)

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
        self.mock_status_list = [200, 500]

        response = self.api_client.put(self.url, format='json', data=self.content_data)
        self.assertTrue(self.mock_request.called, 'Mock request was never made')
        self.assertEqual(self.mock_request.call_count, 2, 'Mock was not called the correct number of times')
        
        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': self.content_data[0],
                'template': 'image'
            }
        })

        args, kwargs = self.mock_request.call_args_list[1]
        self.assertEqual(args, ('post', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'data': json.dumps({
                'content-ids': [self.content_data[0]],
                'template': 'image',
                'prioritized': False
            })
        })
        self.assertHttpApplicationError(response)
