from django.conf import settings
from apps.utils.views import proxy

def proxy_contentgraph(request, path, query_params=None, raw=False):
    return proxy(
        request,
        path,
        base_url=settings.CONTENTGRAPH_BASE_URL,
        query_params=query_params,
        raw=raw
    )

def proxy_store(request, store_id=None, query_params=None, raw=False):
    path = '/store/%s' % store_id
    return proxy_contentgraph(
        request,
        path,
        query_params=query_params,
        raw=raw
    )

def proxy_page(request, store_id, page_id=None, query_params=None, raw=False):
    path = '/store/%s/page/%s' % (store_id, page_id)
    return proxy_contentgraph(
        request,
        path,
        query_params=query_params,
        raw=raw
    )

def proxy_product(request, store_id, product_id=None, query_params=None, raw=False):
    path = '/store/%s/product/live/%s' % (store_id, product_id)
    return proxy_contentgraph(
        request,
        path,
        query_params=query_params,
        raw=raw
    )