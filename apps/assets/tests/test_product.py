import mock
import requests

from boto.sqs.message import RawMessage
from django.conf import settings
from django.utils.unittest.case import TestCase

from apps.api.tasks import fetch_queue


class ProductNotificationQueueTestSuite(TestCase):
    """Running these two tests from PyCharm might cause "False is not True"
    and "True is not False" mix-ups. (It might have been an isolated case?)
    """
    @mock.patch('boto.sqs.message.RawMessage.get_body')
    @mock.patch('boto.sqs.connection.SQSConnection.receive_message')
    @mock.patch.object(requests.Session, 'request')
    def test_update_tileconfig_fail(self, mock_request,
                                    mock_receive_message,
                                    mock_get_body):
        """checks if no fake queue item calls the regeneration initiator."""
        raw_body = ''
        def mock_receive_message_side_effect(*args, **kwargs):
            return [RawMessage(body=raw_body)]

        def mock_get_body_side_effect(*args, **kwargs):
            return raw_body

        mock_receive_message.side_effect = mock_receive_message_side_effect
        mock_get_body.side_effect = mock_get_body_side_effect

        queues = settings.AWS_SQS_POLLING_QUEUES[settings.AWS_SQS_REGION_NAME]
        product_update_queue = queues['product-update-notification-queue']

        fetch_queue(product_update_queue, interval=-1)

        # nothing in the 'queue' to process
        self.assertTrue(mock_receive_message.called)
        self.assertTrue(mock_get_body.called)
        self.assertFalse(mock_request.called)


    @mock.patch('boto.sqs.message.RawMessage.get_body')
    @mock.patch('boto.sqs.connection.SQSConnection.receive_message')
    @mock.patch.object(requests.Session, 'request')
    def test_update_tileconfig_success(self, mock_request,
                                       mock_receive_message,
                                       mock_get_body):
        """checks if a fake queue item calls the regeneration initiator."""
        raw_body = '{"page-id": 1, "product-id": 2}'
        def mock_receive_message_side_effect(*args, **kwargs):
            return [RawMessage(body=raw_body)]

        def mock_get_body_side_effect(*args, **kwargs):
            return raw_body

        mock_receive_message.side_effect = mock_receive_message_side_effect
        mock_get_body.side_effect = mock_get_body_side_effect

        queues = settings.AWS_SQS_POLLING_QUEUES[settings.AWS_SQS_REGION_NAME]
        product_update_queue = queues['product-update-notification-queue']

        fetch_queue(product_update_queue, interval=-1)

        # one item in the 'queue' to process
        self.assertTrue(mock_receive_message.called)
        self.assertTrue(mock_get_body.called)
        self.assertTrue(mock_request.called)
        self.assertEqual(mock_request.call_args[0][0], 'get')
