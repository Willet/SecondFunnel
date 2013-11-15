from django.conf import settings
from apps.utils.views import proxy

# TODO: Does it make sense to make a proxy wrapper to automatically add base_url?
# If so, its not a high priority


def proxy_store(request, store_id=None, raw=False):
    path = '/store/%s' % store_id
    return proxy(request, path, base_url=settings.CONTENTGRAPH_BASE_URL, raw)

def proxy_page(request, store_id, page_id=None, raw=False):
    path = '/store/%s/page/%s' % (store_id, page_id)
    return proxy(request, path, base_url=settings.CONTENTGRAPH_BASE_URL, raw)

def proxy_product(request, store_id, product_id=None, raw=False):
    path = '/store/%s/product/live/%s' % (store_id, product_id)
    return proxy(request, path, base_url=settings.CONTENTGRAPH_BASE_URL, raw)