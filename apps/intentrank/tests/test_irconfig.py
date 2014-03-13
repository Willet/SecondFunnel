import json
import mock

from django.utils.unittest.case import TestCase

from apps.api.tests.utils import configure_mock_request
from apps.intentrank.tasks import \
    handle_ir_config_update_notification_message as fn


class IrConfigNotificationQueueTestSuite(TestCase):
    """Tests if the queue makes the page generator generate pages."""
    def test_message_not_json(self):
        res = fn('~~~')
        self.assertFalse('generated-page' in res)

    def test_message_json_with_missing_keys(self):
        res = fn('{}')
        self.assertFalse('generated-page' in res)

        res = fn('{"page-id": "1"}')
        self.assertFalse('generated-page' in res)

        res = fn('{"store-id": "1"}')
        self.assertFalse('generated-page' in res)

        res = fn('{"tile-id": "1"}')
        self.assertFalse('generated-page' in res)

    def test_correct_message_json(self):
        """It is still going to fail, because store 0 page 0 don't exist."""
        res = fn('{"store-id": "0", "page-id": "0"}')
        self.assertFalse('generated-page' in res)

    @mock.patch('apps.static_pages.aws_utils.upload_to_bucket')
    @mock.patch('httplib2.Http.request')
    def test_correct_message_json_mocked(self, mock_request,
                                         mock_upload_to_bucket):

        mock_request = configure_mock_request(mock_request, {
            r'/?store/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    "id": "1",
                    "display_name": "Test",
                    "public-base-url": "http://example.com",
                    "name": "Test",
                    "slug": "test"
                })
            ),
            r'/?store/\d+/page/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({
                    "heroImageMobile": "",
                    "initialResults": [],
                    "url": "test123",
                    "id": "1",
                    "name": "Test 123",
                    "layout": "hero",
                    "store-id": "1",
                    "categories": "[]",
                    "backupResults": []
                })
            ),
            r'/?page/\d+/tile-config': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
            r'/?page/\d+/tile': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            ),
        })

        # pretend you uploaded to s3, size 1234 bytes
        mock_upload_to_bucket.return_value = 1234

        res = fn('{"store-id": "1", "page-id": "1"}')
        self.assertTrue('generated-page' in res)
        self.assertEqual(res['generated-page'], '1')
