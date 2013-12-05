import mock

from django.utils.unittest.case import TestCase

from apps.static_pages.aws_utils import sns_notify


class SNSTestSuite(TestCase):
    @mock.patch('boto.sns.SNSConnection.publish')
    def test_publish(self, mock_publish):
        """checks if the publish call is made successfully."""
        def publish(topic, message, subject=None):
            return {'response': message}

        mock_publish.side_effect = publish

        returns = sns_notify(subject='hello', message='world')

        self.assertEqual(returns['response'], 'world')

    @mock.patch('boto.sns.SNSConnection.publish')
    def test_publish_superlong_message(self, mock_publish):
        """checks if the publish call is made unsuccessfully, if the message
        is too long for the board.
        """
        def publish(topic, message, subject=None):
            return {'response': message}

        mock_publish.side_effect = publish

        with self.assertRaises(ValueError):
            returns = sns_notify(subject='hello', message='world' * 100000)
