import json
import mock
import requests
import random
from tastypie.test import ResourceTestCase, TestApiClient
from apps.api.tests.utils import (AuthenticatedResourceTestCase,
                                  configure_mock_request,
                                  MockedHammockRequestsTestCase,
                                  BaseNotAuthenticatedTests,
                                  BaseMethodNotAllowedTests)
from django.conf import settings

class UnauthenticatedContentTestSuite(ResourceTestCase):
    def test_unauthorized(self):
        response = self.api_client.get(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)

class BaseContentTests(BaseNotAuthenticatedTests, BaseMethodNotAllowedTests):
    def test_valid_calls(self):
        response = self.api_client.post(self.url, data={})

        self.assertMockRequestCallCount(1)
        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('patch', settings.CONTENTGRAPH_BASE_URL + '/store/%s/content/%s' % (self.store_id, self.content_id)))
        self.assertEqual(kwargs, self.expected_data)
        self.assertHttpOK(response)
        self.assertEqual(self.mock_content_default, json.loads(response.content))

        #Setting up new data to be returned
        self.mock_request.reset_mock()
        self.mock_status_default = 500

        response = self.api_client.post(self.url, data={})

        self.assertMockRequestCallCount(1)
        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('patch', settings.CONTENTGRAPH_BASE_URL + '/store/%s/content/%s' % (self.store_id, self.content_id)))
        self.assertEqual(kwargs, self.expected_data)
        self.assertHttpApplicationError(response)
        self.assertEqual(self.mock_content_default, json.loads(response.content))

class RejectContentTests(MockedHammockRequestsTestCase, BaseContentTests):
    def setUp(self):
        super(RejectContentTests, self).setUp()
        self.store_id = 38
        self.content_id = 1077
        self.url = '/graph/v1/store/%s/content/%s/reject' % (self.store_id, self.content_id)
        self.expected_data = {
            'data': json.dumps({
                'status': 'rejected'
            })
        }
        self.allowed_methods = ['post']

class UndecideContentTests(MockedHammockRequestsTestCase, BaseContentTests):
    def setUp(self):
        super(UndecideContentTests, self).setUp()
        self.store_id = 38
        self.content_id = 1077
        self.url = '/graph/v1/store/%s/content/%s/undecide' % (self.store_id, self.content_id)
        self.expected_data = {
            'data': json.dumps({
                'status': 'needs-review'
            })
        }
        self.allowed_methods = ['post']

class ApproveContentTests(MockedHammockRequestsTestCase, BaseContentTests):
    def setUp(self):
        super(ApproveContentTests, self).setUp()
        self.store_id = 38
        self.content_id = 1077
        self.url = '/graph/v1/store/%s/content/%s/approve' % (self.store_id, self.content_id)
        self.expected_data = {
            'data': json.dumps({
                'status': 'approved'
            })
        }
        self.allowed_methods = ['post']

class ContentOperationsTests(MockedHammockRequestsTestCase, BaseNotAuthenticatedTests, BaseMethodNotAllowedTests):
    def setUp(self):
        super(ContentOperationsTests, self).setUp()
        self.page_id = 1
        self.content_id = 1077
        self.url_pattern = '/graph/v1/store/1/page/%s/content/' % self.page_id
        self.url = '%s%s' % (self.url_pattern, self.content_id)
        self.allowed_methods = ['get', 'put', 'delete']
        self.content_data = [
            self.content_id,
            random.randint(1, 1000)
        ]

    def test_put_all_good(self):
        self.mock_content_default = {
            'results': []
        }

        self.mock_content_list = [
            self.mock_content_default,
            self.mock_content_default,
            {
                'id': 4
            },
            {
                'results': [
                    {
                        'id': 4,
                        'template': 'image',
                        'content-ids': [self.content_data[0]]
                    }
                ]
            },
            {
                'results': [
                    {
                        'id': 67,
                        'template': 'image',
                        'content-ids': [self.content_data[1]]
                    }
                ]
            },
            {
                'id': 67
            },
            {
                'results': [
                    {
                        'id': 67,
                        'template': 'image',
                        'content-ids': [self.content_data[1]]
                    }
                ]
            },
        ]

        response = self.api_client.put(self.url, format='json')
        self.assertMockRequestCallCount(4)

        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': str(self.content_data[0]),
                'template': 'image'
            }
        })
        args, kwargs = self.mock_request.call_args_list[1]
        self.assertEqual(args, ('post', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'data': json.dumps({
                'content-ids': [str(self.content_data[0])],
                'template': 'image',
                'prioritized': False
            })
        })
        args, kwargs = self.mock_request.call_args_list[2]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/store/1/content/%s' % (self.content_data[0])))
        self.assertEqual(kwargs, {})
        args, kwargs = self.mock_request.call_args_list[3]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': 4
            }
        })

        self.assertHttpOK(response)

        response = self.api_client.put('%s%s' % (self.url_pattern, self.content_data[1]), format='json')
        self.assertMockRequestCallCount(7)

        args, kwargs = self.mock_request.call_args_list[4]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': str(self.content_data[1]),
                'template': 'image'
            }
        })
        args, kwargs = self.mock_request.call_args_list[5]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/store/1/content/%s' % (self.content_data[1])))
        self.assertEqual(kwargs, {})
        args, kwargs = self.mock_request.call_args_list[6]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': 67
            }
        })

        self.assertHttpOK(response)

    def test_delete_all_good(self):
        self.mock_content_default = {
            'results': []
        }

        self.mock_status_list = [200, 404, 200, 200, 404]

        self.mock_content_list = [
            self.mock_content_default,
            self.mock_content_default,
            {
                'results': [
                    {
                        'id': 67,
                        'template': 'image',
                        'content-ids': [self.content_data[1]]
                    }
                ]
            },
            self.mock_content_default,
            self.mock_content_default
        ]

        response = self.api_client.delete(self.url, format='json')
        self.assertMockRequestCallCount(2)

        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': str(self.content_data[0]),
                'template': 'image'
            }
        })
        args, kwargs = self.mock_request.call_args_list[1]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/store/1/content/%s' % (self.content_data[0])))
        self.assertEqual(kwargs, {})

        self.assertHttpNotFound(response)

        response = self.api_client.delete('%s%s' % (self.url_pattern, self.content_data[1]), format='json')
        self.assertMockRequestCallCount(5)

        args, kwargs = self.mock_request.call_args_list[2]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': str(self.content_data[1]),
                'template': 'image'
            }
        })
        args, kwargs = self.mock_request.call_args_list[3]
        self.assertEqual(args, ('delete', settings.CONTENTGRAPH_BASE_URL +  '/page/%s/tile-config/%s' % (self.page_id, 67)))
        self.assertEqual(kwargs, {})
        args, kwargs = self.mock_request.call_args_list[4]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/store/1/content/%s' % (self.content_data[1])))
        self.assertEqual(kwargs, {})

        self.assertHttpNotFound(response)

    def test_get_all_good(self):
        self.mock_content_default = {
            'results': []
        }

        self.mock_status_list = [404]

        self.mock_content_list = [
            self.mock_content_default,
            {
                'id': 67
            },
            {
                'results': [
                    {
                        'id': 67,
                        'template': 'image',
                        'content-ids': [self.content_data[1]]
                    }
                ]
            }
        ]

        response = self.api_client.get(self.url, format='json')
        self.assertMockRequestCallCount(1)

        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/store/1/content/%s' % (self.content_data[0])))
        self.assertEqual(kwargs, {})

        self.assertHttpNotFound(response)

        response = self.api_client.get('%s%s' % (self.url_pattern, self.content_data[1]), format='json')
        self.assertMockRequestCallCount(3)

        args, kwargs = self.mock_request.call_args_list[1]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/store/1/content/%s' % (self.content_data[1])))
        self.assertEqual(kwargs, {})

        args, kwargs = self.mock_request.call_args_list[2]
        self.assertEqual(args, ('get', settings.CONTENTGRAPH_BASE_URL + '/page/%s/tile-config' % (self.page_id)))
        self.assertEqual(kwargs, {
            'params': {
                'content-ids': 67
            }
        })

        self.assertHttpOK(response)

    def test_put_remote_failures(self):
        self.mock_status_default = 500

        response = self.api_client.put(self.url, format='json')
        self.assertMockRequestCallCount(1)
        self.assertHttpApplicationError(response)

    def test_delete_remote_failures(self):
        self.mock_status_default = 500

        response = self.api_client.delete(self.url, format='json')
        self.assertMockRequestCallCount(1)
        self.assertHttpApplicationError(response)

    def test_get_remote_failires(self):
        self.mock_status_default = 500

        response = self.api_client.get(self.url, format='json')
        self.assertMockRequestCallCount(1)
        self.assertHttpApplicationError(response)

# TODO: How can we better name these test methods?
# TODO: Should we have separate test folders for different cases instead?
# TODO: Move mock_request dictionaries somewhere else.
class AuthenticatedContentTestSuite(AuthenticatedResourceTestCase):
    @mock.patch('httplib2.Http.request')
    def test_get_all_content(self, mock_request):
        """tests the response when attempting to retrieve all content
        from a page.

        """
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.get('/graph/v1/store/1/page/1/content',
            format='json')

        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_get_by_product_id(self, mock_request):
        """Test for proxy URL returning something."""
        mock_request = configure_mock_request(mock_request, {
            r'/store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'/page/\d+/tile-config/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({"results": [
                    {
                        'id': "65",
                        'content-ids': [32]
                    },
                    {
                        'id': "64",
                        'content-ids': [22]
                    },
                    {
                        'id': "63",
                        'content-ids': [9998]
                    }], "meta": {}})
            ),
            r'/store/\d+/content/?\?tagged-products=\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({"results": [], "meta": {}})
            ),
        })

        response = self.api_client.get(
            '/graph/v1/store/38/page/97/content/suggested',
            format='json'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)
        # TODO: Verify that data is correct?
        # Previously: is_valid = len(json.loads(resp.content)['results']) > 0

class AuthenticatedContentTagTestSuite(AuthenticatedResourceTestCase):

    @mock.patch('httplib2.Http.request')
    def test_content_tag_get(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/content/\d+/tag/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps(["1", "2", "3"])
            ),
        })

        response = self.api_client.get(
            '/graph/v1/store/1/content/1/tag',
            format='json'
        )
        self.assertHttpOK(response)


    @mock.patch('httplib2.Http.request')
    def test_content_tag_post(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/content/\d+/tag/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps(["1", "2", "3"])
            ),
        })

        response = self.api_client.post(
            '/graph/v1/store/1/content/1/tag',
            format='json',
            data='4'  # new tag
        )
        self.assertHttpOK(response)  # valid request

    @mock.patch('httplib2.Http.request')
    def test_content_tag_delete(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/content/\d+/tag/?': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})  # not a valid request for DELETE
            ),
            r'store/\d+/content/\d+/tag/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps(["1", "2", "3"])
            ),
        })

        response = self.api_client.delete(
            '/graph/v1/store/1/content/1/tag/2',
            format='json'
        )
        self.assertHttpOK(response)  # successful deletions give 200

        response = self.api_client.delete(
            '/graph/v1/store/1/content/1/tag/2',
            format='json'
        )
        self.assertHttpOK(response)  # test idempotence (also 200)

        response = self.api_client.delete(
            '/graph/v1/store/1/content/1/tag/1234',  # does not exist
            format='json'
        )
        self.assertHttpOK(response)  # also ok (because it is not in the list)

        response = self.api_client.delete(
            '/graph/v1/store/1/content/1/tag/',  # delete with no key
            format='json'
        )
        self.assertHttpBadRequest(response)  # invalid request
