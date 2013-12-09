import json
import mock
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request


class AuthenticatedPageTestSuite(AuthenticatedResourceTestCase):

    @mock.patch('boto.sqs.queue.Queue.write')
    def test_generate_ir_config(self, mock_write):
        def send(*args, **kwargs):
            pass

        mock_write.side_effect = send

        response = self.api_client.post(
            '/graph/v1/store/1/intentrank/1',
            format='json',
            data={}
        )
        self.assertHttpOK(response)

        self.assertTrue(mock_write.called)