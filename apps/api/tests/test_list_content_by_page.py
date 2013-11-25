import json
import re
import mock

from apps.pinpoint.utils import read_a_file
from apps.api.tests.utils import configure_mock_request, AuthenticatedTestCase


class PageContentTest(AuthenticatedTestCase):
    def setUp(self):
        super(PageContentTest, self).setUp()

    @mock.patch('httplib2.Http.request')
    def test_get_all(self, mock_request):
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
    def test_get_one(self, mock_request):
        """tests the response when attempting to retrieve all content
        from a page.

        """
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/page/\d+/content/?': (
                {'status': 200, 'content-type': 'application/json'},
                read_a_file('api/fixtures/store-38-page-97-content.json', '')
            ),
            r'store/\d+/content/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                read_a_file('api/fixtures/store-38-content-915.json', '')
            ),
        })

        response = self.api_client.get('/graph/v1/store/1/page/1/content',
            format='json')
        self.assertHttpOK(response)

        response = self.api_client.get('/graph/v1/store/1/content/915',
            format='json')
        self.assertHttpOK(response)
