from django.test import TestCase
from mock import patch
from tastypie.test import TestApiClient
import json
import random
import string

#TODO: This is almost an exact copy of the rejected tests consider refactoring
class UndecideContentTests(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.client = TestApiClient()
        self.store_id = 38
        self.content_id = 1077
        self.url = '/graph/v1/store/%s/content/%s/undecide' % (self.store_id, self.content_id)

        resp = self.client.post('/graph/v1/user/login/', format='json', data = {
            'username': 'test',
            'password': 'asdf'
        })
        self.response_json = json.dumps({
            'test_key1': 'test_value1',
            'test_key2': 'test_value2',
            #Very unlikely anything hard coded collides with this
            'random_key': ''.join(random.choice(string.ascii_letters + string.digits) for x in range(32))
        })
        self.not_logged_in_json = json.dumps({
            'error': 'Not logged in'
        })
        self.bad_method_json = json.dumps({
            'error': 'Unsupported Method'
        })

        self.call_checks = {
            'http_called': False
        }
        that = self

        from apps.api.views import httplib2
        class TestHttp(httplib2.Http):
            def request(self, uri, method='GET', body=None, headers=None):
                that.call_checks['http_called'] = True
                that.assertEqual(method, 'PATCH')
                that.assertTrue('ApiKey' in headers, 'No api key found in the headers')
                that.assertEqual(headers['ApiKey'], 'secretword')
                that.assertEqual(uri, 'store/%s/content/%s' % (that.store_id, that.content_id))

                try:
                    body = json.loads(body)
                except:
                    that.fail('Body is not valid json')

                that.assertEqual(len(body), 2)
                that.assertTrue('active' in body)
                that.assertEqual(body['active'], True)
                that.assertTrue('approved' in body)
                that.assertEqual(body['approved'], False)

                return [
                    {
                        'status': 200,
                        'content-type': 'application/json'
                    },
                    that.response_json
                ]

        self.mockHttp = TestHttp

    def tearDown(self):
        self.call_checks = {}

    def test_uses_proxy(self):
        from apps.api.views import httplib2
        with patch.object(httplib2, 'Http', self.mockHttp):
            response = self.client.patch(self.url, data={})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.response_json)

        self.assertTrue(self.call_checks['http_called'], 'Proxy server never called')

    def test_not_logged_in(self):
        client = TestApiClient()

        from apps.api.views import httplib2
        with patch.object(httplib2, 'Http', self.mockHttp):
            response = client.patch(self.url, data={})
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.not_logged_in_json)

        self.assertFalse(self.call_checks['http_called'], 'Proxy server was called but user was not logged in')

    def test_bad_methods(self):
        from apps.api.views import httplib2
        with patch.object(httplib2, 'Http', self.mockHttp):
            response = self.client.get(self.url, data={})
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.bad_method_json)

            response = self.client.post(self.url, data={})
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.bad_method_json)

        self.assertFalse(self.call_checks['http_called'], 'Proxy server was called but bad method was used')
