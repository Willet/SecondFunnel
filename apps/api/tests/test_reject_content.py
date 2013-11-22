from django.test import TestCase
from mock import patch
import json

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


class rejectContentTests(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.client = Client2()
        self.url = '/graph/v1/store/38/content/1077'

        resp = self.client.post('/graph/v1/user/login/', content_type='application/json', data = json.dumps({
            'username': 'test',
            'password': 'asdf'
        }))
        self.response_json = json.dumps({
            'test_key1': 'test_value1',
            'test_key2': 'test_value2'
        })

    def tearDown(self):
        pass

    def test_uses_proxy(self):
        that = self
        
        from apps.api.views import httplib2
        class testHttp(httplib2.Http):
            def request(self, uri, method='GET', body=None, headers=None):
                that.assertEqual(method, 'PATCH')
                that.assertTrue('ApiKey' in headers)
                that.assertEqual(headers['ApiKey'], 'secretword')

                return [
                    {
                        'status': 200,
                        'content-type': 'application/json'
                    },
                    that.response_json
                ]

        with patch.object(httplib2, 'Http', testHttp):
        	#make a call that should be proxied
            response = self.client.patch(self.url)

            #assert that the mock data is passed through unchanged
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, self.response_json)
