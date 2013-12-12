import json
import mock
from apps.api.tests.utils import AuthenticatedResourceTestCase, configure_mock_request


class AuthenticatedIrConfigTestSuite(AuthenticatedResourceTestCase):

    @mock.patch('boto.sqs.connection.SQSConnection.get_queue')
    def test_generate_ir_config(self, mock_get_queue):
        store_id = "1"
        ir_id = "1"
        mock_queue = mock_get_queue.return_value

        response = self.api_client.post(
            '/graph/v1/store/{0}/intentrank/{1}'.format(store_id, ir_id),
            format='json',
            data={}
        )
        self.assertHttpOK(response)

        # Verify mock
        self.assertTrue(mock_queue.write.called)

        # TODO: Is there a way to check call args without caring about args vs. kwargs?
        mock_get_queue.assert_called_once_with(queue_name='intentrank-configwriter-worker-queue-test')

        write_args = mock_queue.write.call_args
        args, kwargs = write_args
        message = args[0] # Message is the first arg to `write`

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

    @mock.patch('boto.sqs.connection.SQSConnection.get_queue')
    def test_generate_ir_config_bad_queue(self, mock_get_queue):
        store_id = "1"
        ir_id = "1"

        mock_get_queue.return_value = None

        try:
            response = self.api_client.post(
                '/graph/v1/store/{0}/intentrank/{1}'.format(store_id, ir_id),
                format='json',
                data={}
            )
        except:
            self.fail('Should not throw an exception when queue not found')

        content = json.loads(response.content)

        self.assertHttpApplicationError(response)
        self.assertDictEqual(content, {
            'error': 'No queue found with name intentrank-configwriter-worker-queue-test'
        })
