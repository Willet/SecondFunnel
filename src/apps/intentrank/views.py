from django.conf import settings
from apps.utils.views import proxy

def proxy_intentrank(request, path, query_params=None, raw=False):
    return proxy(
        request,
        path,
        base_url=settings.INTENTRANK_BASE_URL,
        query_params=query_params,
        raw=raw
    )

def proxy_get_results(request, page_id=None, query_params=None, raw=False):
    path = '/intentrank/page/%s/getresults' % page_id
    return proxy_intentrank(
        request,
        path,
        query_params=query_params,
        raw=raw
    )