import json
import mock
import requests
from tastypie.test import ResourceTestCase
from apps.api.tests.utils import (AuthenticatedResourceTestCase,
                                  configure_mock_request,
                                  configure_hammock_request)


class UnauthenticatedScraperTestSuite(ResourceTestCase):
    def test_unauthorized(self):
        response = self.api_client.get(
            # What should URL look like?
            '/graph/v1/scraper/store/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)


class AuthenticatedContentTestSuite(AuthenticatedResourceTestCase):
    @mock.patch.object(requests.Session, 'request')
    def test_get_all_scrapers(self, mock_request):
        mock_request = configure_hammock_request(mock_request, {
            r'/scraper/store/\d+': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    'results': [{'store-id': '1'}, {'store-id': '1'}],
                    'meta': {}
                })
            ),
        })

        response = self.api_client.get(
            '/graph/v1/scraper/store/1'
        )

        self.assertHttpOK(response)
        self.assertValidJSONResponse(response)

        results = json.loads(response.content).get('results')

        self.assertEquals(len(results), 2)
        # TODO: What else to test on a mock?


    @mock.patch.object(requests.Session, 'request')
    def test_delete_scraper(self, mock_request):
        mock_request = configure_hammock_request(mock_request, {
            r'/scraper/store/\d+/.*?/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        response = self.api_client.delete(
            '/graph/v1/scraper/store/1/my-scraper'
        )

        self.assertHttpOK(response)