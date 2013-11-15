from django.conf import settings
from apps.utils.views import proxy


def proxy_get_results(request, page_id=None, raw=False):
    path = '/intentrank/page/%s/getresults' % page_id
    return proxy(request, path, base_url=settings.CONTENTGRAPH_BASE_URL, raw)