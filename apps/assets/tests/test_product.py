import mock

from boto.sqs.message import RawMessage
from django.conf import settings
from django.utils.unittest.case import TestCase

from apps.api.tasks import fetch_queue


class ProductNotificationQueueTestSuite(TestCase):
    """Running these two tests from PyCharm might cause "False is not True"
    and "True is not False" mix-ups. (It might have been an isolated case?)
    """
    @mock.patch('apps.static_pages.aws_utils.sqs_poll')
    @mock.patch('apps.contentgraph.models.TileConfigObject'
                '.mark_tile_for_regeneration')
    def test_update_tileconfig_fail(self, mocked_method, mock_poll):
        """checks if no fake queue item calls the regeneration initiator."""
        def side(*args, **kwargs):
            return []
        mock_poll.side_effect = side

        queues = settings.AWS_SQS_POLLING_QUEUES[settings.AWS_SQS_REGION_NAME]
        product_update_queue = queues['product-update-notification-queue']

        fetch_queue(product_update_queue, interval=-1)

        # nothing in the 'queue' to process
        self.assertFalse(mocked_method.called)


    @mock.patch('apps.static_pages.aws_utils.sqs_poll')
    @mock.patch('apps.contentgraph.models.TileConfigObject'
                '.mark_tile_for_regeneration')
    def test_update_tileconfig_success(self, mocked_method, mock_poll):
        """checks if a fake queue item calls the regeneration initiator."""
        def side(*args, **kwargs):
            return [RawMessage(body='{"page-id": 1, "product-id": 2}')]
        mock_poll.side_effect = side

        queues = settings.AWS_SQS_POLLING_QUEUES[settings.AWS_SQS_REGION_NAME]
        product_update_queue = queues['product-update-notification-queue']

        fetch_queue(product_update_queue, interval=-1)

        # one item in the 'queue' to process
        self.assertTrue(mocked_method.called)
