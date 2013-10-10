import json
from apps.intentrank.utils import ajax_jsonp

from django.http import HttpResponse

from apps.contentgraph.models import ContentGraphObject, get_contentgraph_data


def get_store(store_id):
    return ContentGraphObject('/store/{0}'.format(store_id))


def view_store(request, store_id):
    return ajax_jsonp(get_store(store_id))


def get_stores():
    """get all stores (for which that you have access;
    this is not the case yet).
    """
    stores = []
    data = get_contentgraph_data('/store')
    for store in data['results']:  # json format: {"results": [...]}
        stores.append(get_store(store['id']))
    return stores


def view_stores(request):
    return ajax_jsonp(get_stores())


def get_page(store_id, page_id):
    return ContentGraphObject('/store/{0}/page/{1}'.format(
        store_id, page_id))


def view_page(request, store_id, page_id):
    return ajax_jsonp(get_page(store_id, page_id))


def get_pages(store_id):
    pages = []
    data = get_contentgraph_data('/store/{0}/page'.format(store_id))
    for page in data['results']:  # json format: {"results": [...]}
        pages.append(get_page(store_id, page['id']))
    return pages


def view_pages(request, store_id):
    return ajax_jsonp(get_pages(store_id))


def get_product(store_id, page_id, product_id):
    """TODO: check if endpoint outputs are consistent with pages/stores"""
    return ContentGraphObject('/store/{0}/page/{1}/product/{2}'.format(
        store_id, page_id, product_id))


def view_product(request, store_id, page_id, product_id):
    """TODO: check if endpoint outputs are consistent with pages/stores"""
    return ajax_jsonp(get_product(store_id, page_id, product_id))


def get_products(store_id, page_id):
    """TODO: check if endpoint outputs are consistent with pages/stores"""
    products = []
    data = get_contentgraph_data('/store/{0}/page/{1}/product'.format(
        store_id, page_id))
    for product in data['results']:  # json format: {"results": [...]}
        products.append(get_product(store_id, product['id']))
    return products


def view_products(request, store_id, page_id):
    return ajax_jsonp(get_products(store_id, page_id))


def proxy(request, endpoint_path='/'):
    """generic version of all view_defs.

    Simply relays the call to the backend and sends the exact data back.
    """
    return HttpResponse(get_contentgraph_data(endpoint_path))


def poke(request):
    from apps.contentgraph.models import ContentGraphObject

    a = ContentGraphObject(request.GET.get('url'))

    return HttpResponse(json.dumps(a.cached_data))