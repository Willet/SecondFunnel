import json
import mock

from django.utils.unittest.case import TestCase
from apps.pinpoint.tasks import \
    handle_tile_generator_update_notification_message as fn


class TileConfigTestSuite(TestCase):
    """Tests the dequeuing-queuing process, and checks if incorrect messages
    are handled with an error response.

    the actual generate_ir_config method is tested elsewhere.
    """

    def test_message_not_json(self):
        res = fn('~~~')
        self.assertFalse('scheduled-page' in res)

    def test_message_json_with_missing_keys(self):
        res = fn('{}')
        self.assertFalse('scheduled-page' in res)

        res = fn('{"page-id": "1"}')
        self.assertFalse('scheduled-page' in res)

        res = fn('{"store-id": "1"}')
        self.assertFalse('scheduled-page' in res)

        res = fn('{"tile-id": "1"}')
        self.assertFalse('scheduled-page' in res)

    @mock.patch('boto.sqs.queue.Queue.write')  # to prevent queuing
    def test_correct_message_json(self, mock_send_message):

        def dummy_message(*args, **kwargs):
            return {'page-id': '1'}

        mock_send_message.side_effect = dummy_message

        res = fn('{"store-id": "1", "page-id": "1"}')
        self.assertTrue('scheduled-page' in res)
        self.assertEqual(res['scheduled-page'], '1')
