import json
import mock

from apps.api.tests.utils import (AuthenticatedResourceTestCase,
                                  configure_mock_request)


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
