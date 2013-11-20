from tastypie.test import ResourceTestCase


class ContentProxyTest(ResourceTestCase):
    def setUp(self):
        super(ContentProxyTest, self).setUp()

        self.username = 'nterwoord'
        self.password = 'asdf'

    def tearDown(self):
        pass

    def get_credentials(self):
        return self.create_basic(username=self.username, password=self.password)

    def test_unauthorized(self):
        response = self.api_client.get(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)