import httplib2
import json

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import (HttpResponse, HttpResponseBadRequest)
from django.conf import settings

from apps.api.decorators import check_login, append_headers, request_methods


# login_required decorator?
@never_cache
@csrf_exempt
@request_methods('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH')
def proxy_tile(request, store_id, page_id, object_type='product', object_id=''):
    """generates or deletes tiles and tileconfigs for either the
    product or content that is being passed into this function.
    """

    # not the complete http verb list -- just the ones we know for sure
    # we support.
    allowed_object_types = ['product', 'content']

    if not request.user or not request.user.is_authenticated():
        return HttpResponse(
            content='{"error": "Not logged in"}',
            content_type='application/json',
            status=401
        )

    if not object_id or not object_type in allowed_object_types:
        # we only support product or content right now, and it requires an id
        return HttpResponseBadRequest()

    request_body = json.loads(request.body or '{}')

    object_url = 'store/{store_id}' \
                 '/page/{page_id}' \
                 '/{object_type}/{object_id}'.format(
        store_id=store_id,
        page_id=page_id,
        object_type=object_type,
        object_id=object_id)

    tile_config_url = 'page/{page_id}/tile-config'.format(
        page_id=page_id,
    )

    tile_url = 'page/{page_id}/tile'.format(
        page_id=page_id,
    )

    response = content_request(object_url, method=request.method)

    # could not get the object itself.
    if response.status_code == 500:
        return response

    if request.method == 'PUT':
        request.method = 'POST'  # tileconfig doesn't accept PUTs right now

    # create corresponding tile config
    response = tile_config_request(url=tile_config_url,
        object_type=object_type, object_id=object_id,
        method=request.method, data=request_body)

    # could not (verb|create) a tile config for this object.
    if response.status_code == 500:
        return response

    # tileconfig request returns a tile. create corresponding tile
    response = tile_request(url=tile_url,
        method=request.method, data=response.content)

    return response


# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view
def proxy_request(path, verb='GET', query_string=None, body=None, headers=None):
    if not headers:
        headers = {}

    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)

    if query_string:
        url += '?' + query_string

    if not headers.get('ApiKey', None):
        headers['ApiKey'] = 'secretword'

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=verb,
        body=body,
        headers=headers
    )

    return HttpResponse(
        content=content,
        status=int(response['status']),
        content_type=response['content-type']
    )


def content_request(content_url, method='GET'):
    response = proxy_request(
        content_url,
        verb=method
    )

    if not (200 <= response.status_code < 300):
        response.status_code = 500

    return response


def tile_config_request(url, object_id, object_type='product',
                        method='POST', data=None):
    """By default (POST), creates a tile config for a product, or
    a piece of content.
    """

    object_template = object_type  # i.e. products use the product template
    if object_type == 'content':
        object_template = 'image'  # content uses youtube/video/image templates, default to image

    response = proxy_request(
        url,
        verb=method,
        body=json.dumps({
            'template': data.get('template', object_template),
            '%s-ids' % object_type: [object_id]
        })
    )

    # Should we do some amalgamated response?
    # I don't think the response is used, so just return for now
    if not (200 <= response.status_code < 300):
        response.status_code = 500

    return response


def tile_request(url, method='POST', data=None):
    """By default, POSTs a tile to the page's tile url.

    :param data the json tile as a string.
    :type data str
    """

    response = proxy_request(
        url,
        verb=method,
        body=data
    )

    # Should we do some amalgamated response?
    # I don't think the response is used, so just return for now
    if not (200 <= response.status_code < 300):
        response.status_code = 500

    return response


@never_cache
@csrf_exempt
def proxy_view(request, path):
    """Throw an exception for every unhandled request from CM."""
    raise NotImplementedError("'{0}' has not yet been implemented".format(path))
