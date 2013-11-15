from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import httplib2

# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view

# Nick is not a security expert.
# He does, however, recommend we read up security policy to see if using
# CORS is sufficient to prevent against CSRF, because he is having a hard time
# handling that...
@never_cache
@csrf_exempt
def proxy(request, path, base_url=None, raw=False):
    # Normally, we would use the login_required decorator, but it will
    # redirect on fail. Instead, just do the check manually; side benefit: we
    # can also return something more useful
    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(
            content='{"error": "Not logged in"}',
            content_type='application/json',
            status=401
        )

    if not base_url:
        url = path
    else:
        url = '%s/%s' % (base_url, path)

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

    if raw:
        return (response, content)
    else:
        return HttpResponse(
            content=content,
            status=response['status'],
            content_type=response['content-type']
        )