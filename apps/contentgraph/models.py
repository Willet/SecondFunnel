import hammock
import json
import httplib2

from django.conf import settings


# this is a copy
ContentGraphClient = hammock.Hammock(settings.CONTENTGRAPH_BASE_URL,
                                     headers={'ApiKey': 'secretword'})


def get_contentgraph_data(endpoint_path, headers=None, method="GET", body=""):
    """Wraps all contentgraph requests with the required api key.

    return will be a json dict, or a string if deserialization fails.
    """
    def is_valid_response(status):
        # wild guess (HTTP 200 series are usually valid)
        return 200 <= int(status) < 300

    if not headers:
        headers = {}

    # it will get fancier over time
    headers.update({'ApiKey' : 'secretword'})

    http = httplib2.Http()
    response, content = http.request(
        settings.CONTENTGRAPH_BASE_URL + endpoint_path, method=method,
        body=body, headers=headers)

    # possible ValueError intentionally propagated
    if is_valid_response(response['status']):
        return json.loads(content)

    if response['status'] == '401':
        raise ValueError('401 Requested object requires authentication')

    if response['status'] == '403':
        raise ValueError('403 Requested object is not accessible')

    if response['status'] == '404':
        raise ValueError('404 Requested object does not exist')

    if response['status'] == '405':
        raise ValueError('405 Method does not work on request object')

    # try to return something in all other cases
    try:
        return json.loads(content)
    except:
        return None


class ContentGraphObject(object):
    """object representation of any CG endpoint.

    This object is not bound to a database, and cannot be saved unless data
    is transferred to another model.
    """
    endpoint_path = '/'
    cached_data = {}

    def __init__(self, endpoint_path, auto_create=False):
        """supply a path to connect to, e.g. /store/126.

        @param {boolean} auto_create        create this object if it is missing
        """
        self.endpoint_path = endpoint_path
        if auto_create:
            get_contentgraph_data(endpoint_path=endpoint_path, method="PUT",
                                  body=json.dumps({}))

        self.cached_data = get_contentgraph_data(endpoint_path=self.endpoint_path)

    def data(self):
        if self.cached_data:
            result = self.cached_data
        else:
            result = get_contentgraph_data(endpoint_path=self.endpoint_path)
            self.cached_data = result

        return self.cached_data

    def get(self, item, default_value=None):
        # dict method
        return self.data().get(item, default_value)

    def set(self, key, value):
        if key == 'endpoint_path':
            return

        # apparently, objects with __setattr__ just skip over this
        setattr(self, key, value)

        # send it back to the server
        return get_contentgraph_data(endpoint_path=self.endpoint_path,
            method="PATCH", body=json.dumps({key: value}))

    def json(self, serialized=True):
        if serialized:
            return json.dumps(self.cached_data)
        else:
            return self.cached_data


class TileConfigObject(object):
    """Suppose the tile config generator does something. This object
    is a pseudo-controller that tells the real generator to do stuff.
    """

    client = None

    def __init__(self, page_id=-1):
        self.client = ContentGraphClient.page(page_id)('tile-config')

    def get_all(self):
        """Get all configs for this page.

        @returns {list}
        @raises IndexError
        """
        return self.client.GET().json()['results']

    def get(self, config_id):
        """Get one config.

        @returns {dict}
        @raises IndexError
        """
        return self.client(config_id).GET().json()

    def update_config(self, config_id, new_props):
        """merges a dict given with the existing tile config."""
        return self.client(config_id).PATCH(data=json.dumps(new_props)).json()

    def regenerate_product_tiles(self, product_id):
        """Mark all tile configs for this product for regeneration."""
        # list
        tile_configs = self.client.GET(params={'product-ids': product_id})\
            .json()['results']

        # dicts
        for tile_config in tile_configs:
            # yes, a string 'true'
            self.client(tile_config['id']).PATCH(data={'regenerate': 'true'})

    def regenerate_content_tiles(self, content_id):
        """Mark all tile configs for this content for regeneration."""
        # list
        tile_configs = self.client.GET(params={'content-ids': content_id})\
            .json()['results']

        # dicts
        for tile_config in tile_configs:
            # yes, a string 'true'
            self.client(tile_config['id']).PATCH(data={'regenerate': 'true'})
