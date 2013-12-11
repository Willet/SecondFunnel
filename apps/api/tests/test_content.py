import json
import mock
import requests
from tastypie.test import ResourceTestCase, TestApiClient
from apps.api.tests.utils import (AuthenticatedResourceTestCase,
                                  configure_mock_request,
                                  configure_hammock_request,
                                  MockedHammockRequestsTestCase)
from django.conf import settings

class UnauthenticatedContentTestSuite(ResourceTestCase):
    def test_unauthorized(self):
        response = self.api_client.get(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)

class RejectContentTests(MockedHammockRequestsTestCase):
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

    def test_valid_rejections(self):
        response = self.api_client.post(self.url, data={})

        self.assertTrue(self.mock_request.called, 'Mock request was never made')
        self.assertEqual(self.mock_request.call_count, 1, 'Mock was not called the correct number of times')
        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('patch', settings.CONTENTGRAPH_BASE_URL + '/store/%s/content/%s' % (self.store_id, self.content_id)))
        self.assertEqual(kwargs, self.expected_data)
        self.assertHttpOK(response)
        self.assertEqual(self.mock_content_default, json.loads(response.content))

        #Setting up new data to be returned
        self.mock_request.reset_mock()
        self.mock_status_default = 500

        response = self.api_client.post(self.url, data={})

        self.assertTrue(self.mock_request.called, 'Mock request was never made')
        self.assertEqual(self.mock_request.call_count, 1, 'Mock was not called the correct number of times')
        args, kwargs = self.mock_request.call_args_list[0]
        self.assertEqual(args, ('patch', settings.CONTENTGRAPH_BASE_URL + '/store/%s/content/%s' % (self.store_id, self.content_id)))
        self.assertEqual(kwargs, self.expected_data)
        self.assertHttpApplicationError(response)
        self.assertEqual(self.mock_content_default, json.loads(response.content))

    def test_not_authenticated(self):
        client = TestApiClient()
        response = client.post(self.url, format='json', data={})

        self.assertFalse(self.mock_request.called, 'Mock request was still called when user was not logged in')
        self.assertEqual(self.mock_request.call_count, 0)

        self.assertHttpUnauthorized(response)
        self.assertEqual(response._headers['content-type'][1], 'application/json')
        self.assertEqual(json.dumps({
            'error': 'Not logged in'
        }), response.content)

    def test_bad_method(self):
        verbs = {
            'get': None,
            'put': {},
            'patch': {},
            'delete': None
        }

        for verb in verbs:
            response = getattr(self.api_client, verb)(self.url, format='json', data=verbs[verb])
            self.assertFalse(self.mock_request.called, 'Mock request was still called when bad method was used')
            self.assertEqual(self.mock_request.call_count, 0)
            self.assertHttpMethodNotAllowed(response)

# TODO: How can we better name these test methods?
# TODO: Should we have separate test folders for different cases instead?
# TODO: Move mock_request dictionaries somewhere else.
class AuthenticatedContentTestSuite(AuthenticatedResourceTestCase):
    @mock.patch('httplib2.Http.request')
    def test_add_content_success(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        # TODO: Make URL pattern a 'constant' in somewhere relevant
        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_add_content_proxy_add_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

    @mock.patch('httplib2.Http.request')
    def test_add_content_tileconfig_add_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile': (
                {'status': 500, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

    @mock.patch('httplib2.Http.request')
    def test_remove_content_success(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.delete(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_remove_content_proxy_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        response = self.api_client.delete(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

    @mock.patch('httplib2.Http.request')
    def test_remove_content_tile_config_fail(self, mock_request):
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile-config': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'page/\d+/tile': (
                {'status': 400, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.delete(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )

        self.assertHttpApplicationError(response)

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
    def test_get_single_content(self, mock_request):
        """tests the response when attempting to retrieve all content
        from a page.

        """
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'store/\d+/content/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.get('/graph/v1/store/1/page/1/content',
            format='json')
        self.assertHttpOK(response)

        response = self.api_client.get('/graph/v1/store/1/content/915',
            format='json')
        self.assertHttpOK(response)

    @mock.patch('httplib2.Http.request')
    def test_get_by_product_id(self, mock_request):
        """Test for proxy URL returning something."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/suggested/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'/store/\d+/page/\d+/product/ids/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({"results": ["65", "64", "63"], "meta": {}})
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

    @mock.patch.object(requests.Session, 'request')
    def test_valid_undecide(self, mock_request):
        mock_request = configure_hammock_request(mock_request, {
            r'store/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.post(
            '/graph/v1/store/38/content/1077/undecide',
            data={}
        )
        self.assertHttpOK(response)

    @mock.patch.object(requests.Session, 'request')
    def test_invalid_undecide(self, mock_request):
        mock_request = configure_hammock_request(mock_request, {
            r'store/\d+/content/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.get(
            '/graph/v1/store/38/content/1077/undecide',
            data={}
        )
        self.assertHttpMethodNotAllowed(response)
        # If we want, we can verify JSON response as well

        response = self.api_client.patch(
            '/graph/v1/store/38/content/1077/undecide',
            data={}
        )
        self.assertHttpMethodNotAllowed(response)


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
