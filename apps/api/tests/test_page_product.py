import json
import re
import mock

from apps.api.tests.utils import configure_mock_request, AuthenticatedTestCase


class PageProductProxyTest(AuthenticatedTestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(PageProductProxyTest, self).setUp()

    @mock.patch('httplib2.Http.request')
    def test_page_product_delete(self, mock_request):
        returns = [[1, 2], [1]]

        def side_effect(*args, **kwargs):
            result = returns.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        mock_request.side_effect = side_effect

        response = self.api_client.delete('/graph/v1/store/1/page/1/product/1',
            format='json')

        self.assertHttpOK(response)
