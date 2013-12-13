import json
from unittest import TestCase
from boto.sqs.message import RawMessage
from django.conf import settings
import mock
import requests
from tastypie.test import ResourceTestCase
from apps.api.tasks import fetch_queue
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


class ScraperNotificationQueueTestSuite(TestCase):
    def setUp(self):
        self.region = settings.AWS_SQS_REGION_NAME
        self.queues = settings.AWS_SQS_POLLING_QUEUES[self.region]
        self.queue = self.queues['scraper-notification-queue']
        self.queue_name = self.queue['queue_name']

    @mock.patch('boto.sqs.connection.SQSConnection.receive_message')
    @mock.patch.object(requests.Session, 'request')
    def test_no_messages(self, mock_request, mock_receive_message):

        def no_messages(*args, **kwargs):
            return []

        mock_receive_message.side_effect = no_messages

        results = fetch_queue(self.queue, interval=-1)

        self.assertFalse(mock_request.called)
        self.assertEquals(0, len(results[self.region][self.queue_name]))

    # @mock.patch('boto.sqs.message.RawMessage.get_body')
    # @mock.patch('boto.sqs.connection.SQSConnection.receive_message')
    # @mock.patch.object(requests.Session, 'request')
    # def test_bad_message(self, mock_request, mock_receive_message,
    #                      mock_get_body):
    #     results = fetch_queue(self.queue, interval=-1)
    #
    #     # Verify results are empty; shouldn't do anything if message is bad
    #
    @mock.patch('boto.sqs.message.RawMessage.get_body')
    @mock.patch('boto.sqs.connection.SQSConnection.receive_message')
    @mock.patch.object(requests.Session, 'request')
    def test_good_message(self, mock_request, mock_receive_message,
                         mock_get_body):
        message = RawMessage(json.dumps({
           "scraper-id": "1",
           "status": "finished",
           "message": "..."
        }))

        def messages(*args, **kwargs):
            return [message]

        mock_receive_message.side_effect = messages

        results = fetch_queue(self.queue, interval=-1)

        self.assertFalse(mock_request.called)
        self.assertEquals(1, len(results[self.region][self.queue_name]))

        result = results[self.region][self.queue_name][0]
        self.assertEquals({}, result)