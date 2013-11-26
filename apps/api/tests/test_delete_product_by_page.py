import mock

from apps.api.tests import test_config as config
from apps.api.tests.utils import AuthenticatedTestCase


class PageProductProxyTest(AuthenticatedTestCase):

    def setUp(self):
        super(PageProductProxyTest, self).setUp()

    @mock.patch('apps.api.views.proxy_view')
    def test_page_product_delete(self, mock_view):
        """checks if the proxy relays the delete call correctly."""
        correct_uri_path = 'store/1/page/1/product/1'

        def request_fn(request, path):
            if request.method == 'DELETE':
                # proxy made the same call that was made to it
                self.assertEqual(path, correct_uri_path)

        mock_view.side_effect = request_fn

        response = self.api_client.delete('%s/%s' % (config.base_url,
                                                     correct_uri_path),
                                          format='json')

        self.assertTrue(mock_view.has_been_called())
