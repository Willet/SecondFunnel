import json
import mock
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request


class AuthenticatedIrConfigTestSuite(AuthenticatedResourceTestCase):

    @mock.patch('boto.sqs.connection.SQSConnection.get_queue')
    def test_generate_ir_config(self, mock_queue):
        store_id = "1"
        ir_id = "1"

        response = self.api_client.post(
            '/graph/v1/store/{0}/intentrank/{1}'.format(store_id, ir_id),
            format='json',
            data={}
        )
        self.assertHttpOK(response)

        # Verify mock
        self.assertTrue(mock_queue.return_value.write.called)

        all_args = mock_queue.return_value.write.call_args
        args, kwargs = all_args
        message = args[0]

        # TODO Verify SQS queue is correct?

        self.assertDictEqual(
            message.get_body(),
            {
                'classname': 'com.willetinc.intentrank.engine.config.worker.ConfigWriterTask',
                'conf': json.dumps({
                    'storeId': store_id,
                    'pageId': ir_id
                })
            }
        )