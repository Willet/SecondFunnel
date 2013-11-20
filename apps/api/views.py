import json
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import httplib2

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

    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)
    if request.META.get('QUERY_STRING', False):
        url += '?' + request.META['QUERY_STRING']

    # There's probably a more pythonic way to do this, but I feel like it would
    # be ugly
    headers = {}
    for key, value in request.META.iteritems():
        if key.startswith('CONTENT'):
            headers[key] = value
        elif key.startswith('HTTP'):
            headers[key[5:]] = value

    if not headers.get('ApiKey', None):
        headers['ApiKey'] = 'secretword'

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=request.method,
        body=request.body or None,
        headers=headers
    )

    return HttpResponse(
        content=content,
        status=response['status'],
        content_type=response['content-type']
    )

# login_required decorator?
@never_cache
@csrf_exempt
def proxy_content(request, store_id, page_id, content_id):
    # http://stackoverflow.com/questions/18930234/django-modifying-the-request-object
    # Also, need to do a check for method type
    request_body = json.loads(request.body or '{}')

    def post():
        # Can we get this changed to POST?
        request.method = 'PUT'
        path_url = 'store/{store_id}/page/{page_id}/content/{content_id}'.format(
            store_id=store_id,
            page_id=page_id,
            content_id=content_id
        )
        response = proxy_view(request, path_url)

        if not (200 <= response.status_code < 300):
            return response

        request.method = 'POST'
        request.body = json.dumps({
            'template': request_body.get('template', 'image'),
            'content-ids': [content_id]
        })
        path_url = 'page/{page_id}/tile-config'.format(
            page_id=page_id,
        )
        response = proxy_view(request, path_url)

        # Should we do some amalgamated response?
        # I don't think the response is used, so just return for now
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