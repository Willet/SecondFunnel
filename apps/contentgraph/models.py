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
    params = {}

    if not headers:
        headers = {}

    headers.update({'ApiKey': 'secretword'})

    # same as the ContentGraphClient above, with variable headers
    contentgraph_client = hammock.Hammock(settings.CONTENTGRAPH_BASE_URL,
        headers=headers)

    while True:
        # getattr used to retrieve GET/POST magic methods
        method_handler = getattr(contentgraph_client(endpoint_path), method)
        response = method_handler(params=params, data=body)

        # raise errors defined by the Requests library (400s, 500s, 600s)
        response.raise_for_status()

        content = response.json()

        # - 'meta' is an object if the call is paginated
        # - 'meta' cannot be an object if the object itself has an
        #       attribute named 'meta' (dynamodb limitation)
        if 'meta' in content:
            if isinstance(content['meta'], dict):  # is CG meta
                if 'cursors' in content['meta'] and 'next' in content['meta']['cursors']:
                    if not isinstance(content['results'], list):
                        # validate and raise, because we love that
                        raise TypeError(
                            'Paginated call expects [results] to be list; '
                            'got [{0}] instead'.format(
                                type(content['results'])))

                    for result in content['results']:
                        yield result
                        params['offset'] = content['meta']['cursors']['next']

                else:  # end of page
                    for result in content['results']:
                        yield result
                    break  # trigger StopIteration
            else:  # is user-defined meta
                yield content
                break  # trigger StopIteration
        else:  # not paginated call
            yield content
            break  # trigger StopIteration


def call_contentgraph(*args, **kwargs):
    """function-alias for the get_contentgraph_data generator.

    Returns one result (the first one by the generator).
    """
    return next(get_contentgraph_data(*args, **kwargs))


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
            call_contentgraph(endpoint_path=endpoint_path, method="PUT",
                              body=json.dumps({}))

        self.cached_data = call_contentgraph(endpoint_path=self.endpoint_path)

    def data(self):
        if self.cached_data:
            result = self.cached_data
        else:
            result = call_contentgraph(endpoint_path=self.endpoint_path)
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
        return call_contentgraph(endpoint_path=self.endpoint_path,
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

    clients = []

    def __init__(self, store_id=None, page_id=None):
        """Supply either store_id or page_id, not both.

        Supplying page_id is faster.
        If store_id is given, performs actions on all pages for the store.
        """
        if page_id:
            # this is only one page
            self.clients = [ContentGraphClient.page(page_id)('tile-config')]
        elif store_id:
            # this is a store worth of pages; TODO actual pagination
            store_pages = ContentGraphClient\
                .store(store_id)\
                .page.GET(params={'select': 'id', 'results': 100000})\
                .json()
            page_ids = [x['id'] for x in store_pages['results']]
            self.clients = [ContentGraphClient.page(page_id)('tile-config')
                            for page_id in page_ids]
        else:  # given none of those
            raise ValueError("Need store_id or page_id")

    def get_all(self):
        """Get all configs for all pages in this client.

        @returns list{list}
        @raises IndexError
        """
        result = []
        for client in self.clients:
            result.append(client.GET().json()['results'])
        return result

    def get(self, config_id):
        """Get one config.

        @returns list{dict}
        @raises IndexError
        """
        result = []
        for client in self.clients:
            result.append(client(config_id).GET().json())
        return result

    def update_config(self, config_id, new_props):
        """merges a dict given with the existing tile config."""
        result = []
        for client in self.clients:
            result.append(client(config_id).PATCH(data=json.dumps(new_props)).json())
        return result

    def mark_tile_for_regeneration(self, content_id=None, product_id=None):
        """Mark all tile configs for this product/content for regeneration.

        If content_id is given, processes that content's tile config.
        If product_id is given, processes that product's tile config.
        """
        if content_id:
            query_key = 'content-ids'
        else:
            query_key = 'product-ids'

        # list
        for client in self.clients:
            tile_configs = client.GET(
                params={query_key: content_id or product_id}).json()['results']

            # dicts
            for tile_config in tile_configs:
                client(tile_config['id']).PATCH(
                    # TODO: might need concurrency checking
                    params={'version': tile_config['last-modified']},
                    data={'stale': 'true'})  # yes, a string 'true'
                # TODO: version/last-modified
