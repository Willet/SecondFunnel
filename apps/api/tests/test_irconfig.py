import json
import mock
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request


class AuthenticatedPageTestSuite(AuthenticatedResourceTestCase):

    @mock.patch('httplib2.Http.request')
    @mock.patch('boto.sqs.connection.SQSConnection.send_message')
    def test_generate_ir_config(self, mock_request, mock_sqs_send):
        """checks if the proxy handles all mocked tile calls."""
        mock_request = configure_mock_request(mock_request, {
            r'store/\d+/intentrank/\d+/?': (
                {'status': 200, 'content-type': 'application/json'},
                json.dumps({})
            )
        })

        def send(*args, **kwargs):
            pass

        mock_sqs_send.side_effect = send

        response = self.api_client.post(
            '/graph/v1/store/1/intentrank/1',
            format='json',
            data={}
        )
        self.assertHttpOK(response)

        self.assertTrue(mock_sqs_send.called)