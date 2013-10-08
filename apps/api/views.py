from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
import httplib2

# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view

@login_required
@csrf_protect
def proxy_view(request, path):
    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)
    if request.META.has_key('QUERY_STRING'):
        url += '?' + request.META['QUERY_STRING']

    # There's probably a more pythonic way to do this, but I feel like it would
    # be ugly
    headers = {}
    for key, value in request.META.iteritems():
        if key.startswith('HTTP') or key.startswith('CONTENT'):
            headers[key] = value

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