import httplib2
import json

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotAllowed
from django.conf import settings

from apps.api.decorators import check_login, append_headers
from apps.intentrank.utils import ajax_jsonp

from resources import ContentGraphClient


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
    CORS is sufficient to prevent against CSRF, because he is having a hard
    time handling that...
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
        contents, _ = get_proxy_results(
            request=request,
            url=content_url % (settings.CONTENTGRAPH_BASE_URL, store_id, product_id))
        for content in contents:
            if not content in results:  # this works because __hash__
                results.append(content)

    return ajax_jsonp({'results': results,
                       'meta': meta})


# login_required decorator?
@never_cache
@csrf_exempt
# not the complete http verb list -- just the ones we know for sure
# we support.
@request_methods('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH')
def proxy_content(request, store_id, page_id, content_id):
    # TODO: Remove duplication
    # Normally, we would use the login_required decorator, but it will
    # redirect on fail. Instead, just do the check manually; side benefit: we
    # can also return something more useful
    if not request.user or not request.user.is_authenticated():
        return HttpResponse(
            content='{"error": "Not logged in"}',
            mimetype='application/json',
            status=401
        )

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


@never_cache
@csrf_exempt
def reject_content(request, store_id, content_id):
    if request.method != 'PATCH':
        return HttpResponse(json.dumps({
            'error': 'Unsupported Method'
        }), content_type='application/json', status=405)

    if not request.user or (not request.user.is_authenticated()):
        return HttpResponse(json.dumps({
            'error': 'Not logged in'
        }), content_type='application/json', status=401)

    url = 'store/%s/content/%s' % (store_id, content_id)
    h = httplib2.Http()
    response, content = h.request(
        url,
        method='PATCH',
        body=json.dumps({
            'active': False,
            'approved': False
        }),
        headers={
            'ApiKey': 'secretword'
        }
    )

    return HttpResponse(
        content=content,
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
        }), content_type='application/json', status=405)

    if not request.user or (not request.user.is_authenticated()):
        return HttpResponse(json.dumps({
            'error': 'Not logged in'
        }), content_type='application/json', status=401)

    url = 'store/%s/content/%s' % (store_id, content_id)
    h = httplib2.Http()
    response, content = h.request(
        url,
        method='PATCH',
        body=json.dumps({
            'active': True,
            'approved': False
        }),
        headers={
            'ApiKey': 'secretword'
        }
    )

    return HttpResponse(
        content=content,
        status=int(response['status']),
        content_type=response['content-type']
    )


def copy_headers_to_response(headers, response):
    for k, v in headers.items():
        if k != 'connection':
            response[k] = v
    return response


def mimic_response(client_response, server_response):
    copy_headers_to_response(client_response.headers, server_response)
    return server_response


@csrf_exempt
def approve_content(request, store_id, content_id):
    payload = json.dumps({'active': True, 'approved': True})

    r = ContentGraphClient.store(store_id).content(content_id).PATCH(payload)

    response = HttpResponse(content=r.content, status=r.status_code)

    return mimic_response(r, response)
