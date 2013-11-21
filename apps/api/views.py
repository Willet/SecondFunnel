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

    # http://stackoverflow.com/questions/18930234/django-modifying-the-request-object
    # Also, need to do a check for method type
    request_body = json.loads(request.body or '{}')

    # Should create a new request instead of leveraging the existing one
    # Especially because can't modify request.body
    def post():
        path_url = 'store/{store_id}/page/{page_id}/content/{content_id}'.format(
            store_id=store_id,
            page_id=page_id,
            content_id=content_id
        )
        # Can we get this changed to POST?
        response = proxy_request(
            path_url,
            verb='PUT'
        )

        if not (200 <= response.status_code < 300):
            response.status_code = 500
            return response

        path_url = 'page/{page_id}/tile-config'.format(
            page_id=page_id,
        )
        response = proxy_request(
            path_url,
            verb='POST',
            body=json.dumps({
                'template': request_body.get('template', 'image'),
                'content-ids': [content_id]
            })
        )

        # Should we do some amalgamated response?
        # I don't think the response is used, so just return for now
        if not (200 <= response.status_code < 300):
            response.status_code = 500

        return response

    DEFAULT_RESPONSE = lambda: HttpResponse(
        json.dumps({
            'error': 'Unsupported Method'
        }),
        status=405
    )

    return {
        'POST': post,
    }.get(request.method, DEFAULT_RESPONSE)()