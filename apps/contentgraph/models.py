import json
import httplib2

from django.conf import settings


def get_contentgraph_data(endpoint_path, headers=None, method="GET", body=""):
    """Wraps all contentgraph requests with the required api key.

    return will be a json dict, or a string if deserialization fails.
    """
    if not headers:
        headers = {}

    headers.update({'ApiKey' : 'secretword'})

    http = httplib2.Http()
    response, content = http.request(
        settings.CONTENTGRAPH_BASE_URL + endpoint_path, method=method,
        body=body, headers=headers)

    # possible ValueError intentionally propagated
    return json.loads(content)


class ContentGraphObject(object):
    """object representation of any CG endpoint."""
    endpoint_path = '/'
    cached_data = {}

    def __init__(self, endpoint_path):
        """supply a path to connect to, e.g. /store/126."""
        self.endpoint_path = endpoint_path
        self.cached_data = get_contentgraph_data(endpoint_path=self.endpoint_path)

    def data(self):
        if self.cached_data:
            result = self.cached_data
        else:
            result = get_contentgraph_data(endpoint_path=self.endpoint_path)
            self.cached_data = result

        return self.cached_data

    def get(self, item):
        return self.data().get(item, None)

    def set(self, key, value):
        if key == 'endpoint_path':
            return

        # apparently, objects with __setattr__ just skip over this
        setattr(self, key, value)

        # send it back to the server
        return get_contentgraph_data(endpoint_path=self.endpoint_path,
            method="PATCH", body=json.dumps({key: value}))

    def json(self):
        return json.dumps(self.cached_data)