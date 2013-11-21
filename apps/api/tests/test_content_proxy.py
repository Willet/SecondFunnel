from tastypie.test import ResourceTestCase


class UnauthenticatedContentProxyTest(ResourceTestCase):
    def setUp(self):
        super(UnauthenticatedContentProxyTest, self).setUp()

    def tearDown(self):
        pass

    def test_unauthorized(self):
        response = self.api_client.get(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpUnauthorized(response)


class ContentProxyTest(ResourceTestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(ContentProxyTest, self).setUp()

        # Presently, doesn't appear to be any create_session_authentication
        # method... so, need to login manually
        response = self.api_client.post(
            '/graph/v1/user/login/',
            format='json',
            data={
                'username': 'test',
                'password': 'asdf'
            }
        )

    def tearDown(self):
        # TODO: Why is trailing slash required?
        self.api_client.post(
            '/graph/v1/user/logout/',
            format='json'
        )

    def test_authorized(self):
        response = self.api_client.post(
            '/graph/v1/store/1/page/1/content/1',
            format='json'
        )
        self.assertHttpOK(response)