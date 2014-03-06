from apps.intentrank.utils import ajax_jsonp

from django.http import HttpResponse

from apps.contentgraph.models import ContentGraphObject, get_contentgraph_data


def get_store(store_id, as_dict=False):
    cgo = ContentGraphObject('store/{0}'.format(store_id))
    if as_dict:
        return cgo.json(False)
    return cgo


def view_store(request, store_id):
    return ajax_jsonp(get_store(store_id))


def get_stores(as_dict=False):
    """get all stores (for which that you have access;
    this is not the case yet).
    """
    stores = []
    data = get_contentgraph_data('store')
    for store in data:  # json format: {"results": [...]}
        cgo = get_store(store['id'])
        if as_dict:
            stores.append(cgo.json(False))
        else:
            stores.append(cgo)
    return stores


def view_stores(request):
    return ajax_jsonp(get_stores())


def get_page(store_id, page_id, as_dict=False):
    cgo = ContentGraphObject('store/{0}/page/{1}'.format(
        store_id, page_id))
    if as_dict:
        return cgo.json(False)
    return cgo


def view_page(request, store_id, page_id):
    return ajax_jsonp(get_page(store_id, page_id))


def get_pages(store_id, as_dict=False):
    pages = []
    for page in get_contentgraph_data('store/{0}/page'.format(store_id)):  # json format: {"results": [...]}
        cgo = get_page(store_id, page['id'])
        if as_dict:
            pages.append(cgo.json(False))
        else:
            pages.append(cgo)
    return pages


def view_pages(request, store_id):
    return ajax_jsonp(get_pages(store_id))


def get_product(product_id, store_id=0, page_id=0, as_dict=False):
    """TODO: check if endpoint outputs are consistent with pages/stores"""
    if page_id:  # get page-specific products
        cgo = ContentGraphObject('/store/{0}/page/{1}/product/{2}'.format(
            store_id, page_id, product_id))
    elif store_id:  # get store-specific products
        cgo = ContentGraphObject('/store/{0}/product/{1}'.format(
            store_id, product_id))
    else:  # get specific product
        cgo = ContentGraphObject('/product/{0}'.format(product_id))

    if as_dict:
        return cgo.json(False)
    return cgo


def view_product(request, product_id, store_id=0, page_id=0):
    """TODO: check if endpoint outputs are consistent with pages/stores"""
    return ajax_jsonp(get_product(store_id, page_id, product_id))


def get_products(store_id=0, page_id=0, as_dict=False):
    """TODO: check if endpoint outputs are consistent with pages/stores"""
    products = []
    if page_id:  # get page-specific products
        data = get_contentgraph_data('store/{0}/page/{1}/product'.format(
            store_id, page_id))
    elif store_id:  # get store-specific products
        data = get_contentgraph_data('store/{0}/product'.format(
            store_id, page_id))
    else:  # get all products
        data = get_contentgraph_data('product')

    for product in data:
        cgo = get_product(store_id, product['id'])
        if as_dict:
            products.append(cgo.json(False))
        else:
            products.append(cgo)
    return products


def view_products(request, store_id=0, page_id=0):
    return ajax_jsonp(get_products(store_id, page_id))


def proxy(request, endpoint_path='/'):
    """generic version of all view_defs.

    Simply relays the call to the backend and sends the exact data back.
    """
    return HttpResponse(get_contentgraph_data(endpoint_path))
