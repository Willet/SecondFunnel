import json
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import request_methods, check_login
from apps.assets.models import Product, ProductImage, Store, Page
from apps.intentrank.utils import returns_json, returns_cg_json


@request_methods('GET', 'POST', 'PATCH', 'DELETE')
@check_login
@never_cache
@csrf_exempt
@returns_cg_json
def handle_product(request, product_id=0, offset=1,
                   results=settings.API_LIMIT_PER_PAGE, obj_attrs=None):
    """Implements the following API patterns:

    GET /product
    GET /product/id
    POST /product
    PATCH /product/id
    DELETE /product/id
    """
    if product_id:
        product = [Product.objects.filter(old_id=product_id)[0]]
    else:
        product = Product.objects.all()

    if not offset:
        offset = 1
    paginator = Paginator(product, results)
    page = paginator.page(offset)
    next_ptr = page.next_page_number() if page.has_next() else None

    # GET /product/id
    if request.method == 'GET' and product_id:
        return page.object_list[0].to_cg_json()
    # GET /product/id
    elif request.method == 'GET':
        return [c.to_cg_json() for c in page.object_list], next_ptr
    # POST /product
    elif request.method == 'POST':
        attrs = json.loads(request.body)
        new_product = Product()
        new_product.update(**attrs)
        if obj_attrs:
            new_product.update(**obj_attrs)
        new_product.save()  # :raises ValidationError
        return new_product.to_cg_json()
    # PATCH /product/id
    elif request.method == 'PATCH' and product_id:
        product = product[0]
        product.update(**json.loads(request.body))
        if obj_attrs:
            product.update(**obj_attrs)
        product.save()  # :raises ValidationError
        return product.to_cg_json()
    # DELETE /product/id
    elif request.method == 'DELETE':
        product = product[0]
        product.delete()
        return HttpResponse(status=200)  # it would be 500 if delete failed
    
    
@request_methods('GET', 'POST', 'PATCH', 'DELETE')
@check_login
@never_cache
@csrf_exempt
@returns_cg_json
def handle_store_product(request, store_id, product_id=0, offset=1,
                         product_set='', results=settings.API_LIMIT_PER_PAGE):
    """Implements the following API patterns:

    GET /store/id/product
    GET /store/id/product/id
    POST /store/id/product
    PATCH /store/id/product/id
    DELETE /store/id/product/id

    :returns (results, next page pointer)
    """
    store = get_object_or_404(Store, old_id=store_id)

    if product_id:  # get this product for this store
        try:
            product = [Product.objects
                              .filter(old_id=product_id, store_id=store.id)[0]]
        except IndexError:
            raise Http404()
    else:  # get all product for this store
        product = (Product.objects
                          .filter(store_id=store.id)
                          .all())

    if not offset:
        offset = 1
    paginator = Paginator(product, results)
    page = paginator.page(offset)
    next_ptr = page.next_page_number() if page.has_next() else None

    # GET /store/id/product/id
    if request.method == 'GET' and product_id:
        return page.object_list[0].to_cg_json(), None
    # GET /store/id/product
    elif request.method == 'GET':
        return [c.to_cg_json() for c in page.object_list], next_ptr
    # POST /store/id/product
    elif request.method == 'POST':
        return handle_product(request=request,
                              obj_attrs={'store_id': store.id})
    # PATCH /store/id/product_id
    elif request.method == 'PATCH' and product_id:
        return handle_product(request=request, product_id=product_id)
    # DELETE /store/id/product_id
    elif request.method == 'DELETE' and product_id:
        return handle_product(request=request, product_id=product_id)


@request_methods('GET', 'POST', 'PATCH', 'DELETE')
@check_login
@never_cache
@csrf_exempt
@returns_cg_json
def handle_store_page_product(request, store_id, page_id, product_id=0,
                              product_set='', offset=1,
                              results=settings.API_LIMIT_PER_PAGE):
    """Implements the following API patterns:

    GET /store/id/page/id/product
    GET /store/id/page/id/product/id
    POST /store/id/page/id/product
    PATCH /store/id/page/id/product/id
    DELETE /store/id/page/id/product/id

    :returns (results, next page pointer)
    """
    page = get_object_or_404(Page, old_id=page_id)
    feed = page.feed
    tile = feed.tiles[0]  # TODO
    store = page.store

    if product_id:  # get this product for this store
        try:
            product = [Product.objects
                              .filter(old_id=product_id, store_id=store.id)[0]]
        except IndexError:
            raise Http404()
    else:  # get all product for this store
        product = (Product.objects
                          .filter(store_id=store.id)
                          .all())

    if not offset:
        offset = 1
    paginator = Paginator(product, results)
    page = paginator.page(offset)
    next_ptr = page.next_page_number() if page.has_next() else None

    # GET /store/id/page/id/product/id
    if request.method == 'GET' and product_id:
        return page.object_list[0].to_cg_json(), None
    # GET /store/id/page/id/product
    elif request.method == 'GET':
        return [c.to_cg_json() for c in page.object_list], next_ptr
    # POST /store/id/page/id/product
    elif request.method == 'POST':
        return handle_product(request=request,
                              obj_attrs={'store_id': store.id,
                                         'tile_id': tile.id})
    # PATCH /store/id/page/id/product/id
    elif request.method == 'PATCH' and product_id:
        return handle_product(request=request, product_id=product_id)
    # DELETE /store/id/page/id/product/id
    elif request.method == 'DELETE' and product_id:
        return handle_product(request=request, product_id=product_id)

