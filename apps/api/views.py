import json
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import httplib2

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
    # Can we get this changed to POST?
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

# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view

# Nick is not a security expert.
# He does, however, recommend we read up security policy to see if using
# CORS is sufficient to prevent against CSRF, because he is having a hard time
# handling that...
@never_cache
@csrf_exempt
def proxy_view(request, path):
    # Normally, we would use the login_required decorator, but it will
    # redirect on fail. Instead, just do the check manually; side benefit: we
    # can also return something more useful
    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(
            content='{"error": "Not logged in"}',
            mimetype='application/json',
            status=401
        )

    query_string = request.META.get('QUERY_STRING', False)

    headers = {}
    for key, value in request.META.iteritems():
        if key.startswith('CONTENT'):
            headers[key] = unicode(value)
        elif key.startswith('HTTP'):
            headers[key[5:]] = unicode(value)

    response = proxy_request(
        path,
        verb=request.method,
        query_string=query_string,
        body=request.body,
        headers=headers
    )

    return response


# login_required decorator?
@never_cache
@csrf_exempt
def proxy_content(request, store_id, page_id, content_id):
    # TODO: Remove duplication
    # Normally, we would use the login_required decorator, but it will
    # redirect on fail. Instead, just do the check manually; side benefit: we
    # can also return something more useful
    if not request.user or (request.user and not request.user.is_authenticated()):
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

    def post():
        # Can we get this changed to POST?
        response = content_request(content_url, method='PUT')

        if response.status_code == 500:
            return response

        response = tile_config_request(
            tile_config_url,
            content_id,
            data=request_body,
            method='POST'
        )

        return response

    def delete():
        response = content_request(content_url, method='DELETE')

        if response.status_code == 500:
            return response

        response = tile_config_request(
            tile_config_url,
            content_id,
            data=request_body,
            method='DELETE'
        )

        return response

    DEFAULT_RESPONSE = lambda: HttpResponse(
        json.dumps({
            'error': 'Unsupported Method'
        }),
        status=405
    )

    return {
        'POST': post,
        'DELETE': delete
    }.get(request.method, DEFAULT_RESPONSE)()