from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import httplib2

# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view

# Nick is not a security expert.
# He does, however, recommend we read up security policy to see if using
# CORS is sufficient to prevent against CSRF, because he is having a hard time
# handling that...
@csrf_exempt
def proxy_view(request, path):
    # Normally, we would use the login_required decorator, but it will
    # redirect on fail. Instead, just do the check manually; side benefit: we
    # can also return something more useful
    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(
            content='{"error": "Not logged in"}',
            mimetype='application/json',
            status=403
        )

    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)
    if request.META.has_key('QUERY_STRING'):
        url += '?' + request.META['QUERY_STRING']

    # There's probably a more pythonic way to do this, but I feel like it would
    # be ugly
    headers = {}
    for key, value in request.META.iteritems():
        if key.startswith('CONTENT'):
            headers[key] = value
        elif key.startswith('HTTP'):
            headers[key[5:]] = value

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