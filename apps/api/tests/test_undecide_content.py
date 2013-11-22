from django.test import TestCase
from mock import patch
import json
import random
import string

#Patch to give django test client the ability to do a PATCH request
from django.test.client import Client, FakePayload, MULTIPART_CONTENT
from urlparse import urlparse, urlsplit

class Client2(Client):
    """
    Construct a second test client which can do PATCH requests.
    """
    def patch(self, path, data={}, content_type=MULTIPART_CONTENT, **extra):
        "Construct a PATCH request."

        patch_data = self._encode_data(data, content_type)

        parsed = urlparse(path)
        r = {
            'CONTENT_LENGTH': len(patch_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   parsed[4],
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input':     FakePayload(patch_data),
        }

        r.update(extra)
        return self.request(**r)


#TODO: This is almost an exact copy of the rejected tests consider refactoring
class undecideContentTests(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.client = Client2()
        self.store_id = 38
        self.content_id = 1077
        self.url = '/graph/v1/store/%s/content/%s/undecide' % (self.store_id, self.content_id)

        resp = self.client.post('/graph/v1/user/login/', content_type='application/json', data = json.dumps({
            'username': 'test',
            'password': 'asdf'
        }))
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
        class testHttp(httplib2.Http):
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

        self.mockHttp = testHttp

    def tearDown(self):
        self.call_checks = {}

    def test_uses_proxy(self):
        from apps.api.views import httplib2
        with patch.object(httplib2, 'Http', self.mockHttp):
            response = self.client.patch(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.response_json)

        self.assertTrue(self.call_checks['http_called'], 'Proxy server never called')

    def test_not_logged_in(self):
        client = Client2()

        from apps.api.views import httplib2
        with patch.object(httplib2, 'Http', self.mockHttp):
            response = client.patch(self.url)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.not_logged_in_json)

        self.assertFalse(self.call_checks['http_called'], 'Proxy server was called but user was not logged in')

    def test_bad_methods(self):
        from apps.api.views import httplib2
        with patch.object(httplib2, 'Http', self.mockHttp):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.bad_method_json)

            response = self.client.post(self.url)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response._headers['content-type'][1], 'application/json')
            self.assertEqual(response.content, self.bad_method_json)

        self.assertFalse(self.call_checks['http_called'], 'Proxy server was called but bad method was used')