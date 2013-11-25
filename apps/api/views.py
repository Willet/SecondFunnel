import httplib2
import json

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotAllowed)
from django.conf import settings

from apps.api.decorators import check_login, append_headers
from apps.intentrank.utils import ajax_jsonp


# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view
def proxy_request(path, verb='GET', query_string=None, body=None, headers={}):
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


def tile_config_request(tile_config_url, content_id, data=None, method='GET'):
    response = proxy_request(
        tile_config_url,
        verb=method,
        body=json.dumps({
            'template': data.get('template', 'image'),
            'content-ids': [content_id]
        })
    )

    # Should we do some amalgamated response?
    # I don't think the response is used, so just return for now
    if not (200 <= response.status_code < 300):
        response.status_code = 500

    return response


def get_proxy_results(request, url, body=None):
    """small wrapper around all api requests to content graph.

    :returns tuple
    :raises (ValueError, IndexError)
    """
    h = httplib2.Http()
    response, content = h.request(url, method=request.method, body=body,
                                  headers=request.NEW_HEADERS or request.META)

    resp_obj = json.loads(content)

    return (resp_obj['results'], resp_obj['meta'])


@append_headers
@check_login
def proxy_view(request, path):
    """Nick is not a security expert.

    He does, however, recommend we read up security policy to see if using
    CORS is sufficient to prevent against CSRF, because he is having a hard time
    handling that...
    """

    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)
    if request.META.get('QUERY_STRING', False):
        url += '?' + request.META['QUERY_STRING']

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=request.method,
        body=request.body or None,
        headers=request.NEW_HEADERS
    )

    return HttpResponse(
        content=content,
        status=response['status'],
        content_type=response['content-type']
    )


@append_headers
@check_login
def get_suggested_content_by_page(request, store_id, page_id):
    """Returns a multiple lists of product content grouped by
    their product id.
    """
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    product_url = "%s/store/%s/page/%s/product/ids?%s" % (
        settings.CONTENTGRAPH_BASE_URL, store_id, page_id,
        request.META.get('QUERY_STRING', ''))
    content_url = "%s/store/%s/content?tagged-products=%s"

    results = []

    product_ids, meta = get_proxy_results(request=request, url=product_url)
    for product_id in product_ids:
        contents, _ = get_proxy_results(request=request,
            url=content_url % (settings.CONTENTGRAPH_BASE_URL, store_id,
                               product_id))
        for content in contents:
            if not content in results:  # this works because __hash__
                results.append(content)

    return ajax_jsonp({'results': results,
                       'meta': meta})


# login_required decorator?
@never_cache
@csrf_exempt
def proxy_content(request, store_id, page_id, content_id):
    """Normally, we would use the login_required decorator, but it will
    redirect on fail. Instead, just do the check manually;

    side benefit: we can also return something more useful
    """

    # not the complete http verb list -- just the ones we know for sure
    # we support.
    # TODO: probably material for alex's decorator
    allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']

    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(
            content='{"error": "Not logged in"}',
            mimetype='application/json',
            status=401
        )

    # not in the list of verbs we explicitly handle
    if not request.method in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

    request_body = json.loads(request.body or '{}')

    content_url = 'store/{store_id}/page/{page_id}/content/{content_id}'.format(
        store_id=store_id,
        page_id=page_id,
        content_id=content_id
    )

    tile_config_url = 'page/{page_id}/tile-config'.format(
        page_id=page_id,
    )

    response = content_request(content_url, method=request.method)

    # assume this relays CG error to user.
    if response.status_code == 500:
        return response

    if request.method == 'PUT':
        request.method = 'POST'  # tileconfig doesn't accept PUTs right now

    response = tile_config_request(
        tile_config_url,
        content_id,
        data=request_body,
        method=request.method
    )

    return response


# login_required decorator?
@never_cache
@csrf_exempt
def proxy_tile(request, store_id, page_id, object_type, object_id):
    """generates or deletes tiles and tileconfigs for either the
    product or content that is being passed into this function.
    """

    # not the complete http verb list -- just the ones we know for sure
    # we support.
    # TODO: probably material for alex's decorator
    allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
    allowed_object_types = ['product', 'content']

    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(
            content='{"error": "Not logged in"}',
            mimetype='application/json',
            status=401
        )

    if not object_type in allowed_object_types:
        # we only support product or content right now
        return HttpResponseBadRequest()

    request_body = json.loads(request.body or '{}')

    # not in the list of verbs we explicitly handle
    if not request.method in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

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

    response = content_request(object_url, method=request.method)

    # assume this relays CG error to user.
    if response.status_code == 500:
        return response

    if request.method == 'PUT':
        request.method = 'POST'  # tileconfig doesn't accept PUTs right now

    response = tile_config_request(
        tile_config_url,
        object_id,
        data=request_body,
        method=request.method
    )

    return response


@never_cache
@csrf_exempt
def reject_content(request, store_id, content_id):
    if request.method != 'PATCH':
        return HttpResponse(json.dumps({
            'error': 'Unsupported Method'
        }), content_type='application/json', status = 405)

    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(json.dumps({
            'error': 'Not logged in'
        }), content_type = 'application/json', status = 401)

    url = 'store/%s/content/%s' % (store_id, content_id)
    h = httplib2.Http()
    response, content = h.request(
            url,
            method = 'PATCH',
            body = json.dumps({
                'active': False,
                'approved': False
            }),
            headers = {
                'ApiKey': 'secretword'
            }
        )

    return HttpResponse(
        content = content,
        status=int(response['status']),
        content_type=response['content-type']
    )


#TODO: almost exactly the same as reject content. Consider refactoring
@never_cache
@csrf_exempt
def undecide_content(request, store_id, content_id):
    if request.method != 'PATCH':
        return HttpResponse(json.dumps({
            'error': 'Unsupported Method'
        }), content_type='application/json', status = 405)

    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(json.dumps({
            'error': 'Not logged in'
        }), content_type = 'application/json', status = 401)

    url = 'store/%s/content/%s' % (store_id, content_id)
    h = httplib2.Http()
    response, content = h.request(
            url,
            method = 'PATCH',
            body = json.dumps({
                'active': True,
                'approved': False
            }),
            headers = {
                'ApiKey': 'secretword'
            }
        )

    return HttpResponse(
        content = content,
        status=int(response['status']),
        content_type=response['content-type']
    )
