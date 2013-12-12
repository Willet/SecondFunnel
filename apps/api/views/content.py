import json

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotAllowed)
from django.conf import settings

from apps.api.decorators import check_login, append_headers, request_methods
from apps.intentrank.utils import ajax_jsonp

from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response, get_proxy_results


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def reject_content(request, store_id, content_id):
    payload = json.dumps({'status': 'rejected'})

    r = ContentGraphClient.store(store_id).content(content_id).PATCH(payload)

    response = HttpResponse(content=r.content, status=r.status_code)

    return mimic_response(r, response)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def undecide_content(request, store_id, content_id):
    payload = json.dumps({'status': 'needs-review'})

    r = ContentGraphClient.store(store_id).content(content_id).PATCH(payload)

    response = HttpResponse(content=r.content, status=r.status_code)

    return mimic_response(r, response)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def approve_content(request, store_id, content_id):
    payload = json.dumps({'status': 'approved'})

    r = ContentGraphClient.store(store_id).content(content_id).PATCH(payload)

    response = HttpResponse(content=r.content, status=r.status_code)

    return mimic_response(r, response)


@request_methods('PUT')
@check_login
@never_cache
@csrf_exempt
def add_all_content(request, store_id, page_id):
    try:
        content_ids = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=500)

    if type(content_ids) != type([]):
        return HttpResponse(status=500)

    for content_id in content_ids:
        if type(content_id) != type(1):
            return HttpResponse(status=500)

        r = ContentGraphClient.store(store_id).page(
            page_id).content(content_id).PUT('')

        if r.status_code != 200:
            return HttpResponse(status=500)

    return HttpResponse()


@append_headers
@check_login
@never_cache
@csrf_exempt
def get_suggested_content_by_page(request, store_id, page_id):
    """Returns a multiple lists of product content grouped by
    their product id.
    """
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    product_url = "%s/store/%s/page/%s/product/ids?%s" % (
        settings.CONTENTGRAPH_BASE_URL, store_id, page_id,
        request.META.get('QUERY_STRING', ''))
    content_url = "%s/store/%s/content?tagged-products=%s"

    results = []

    product_ids, meta = get_proxy_results(request=request, url=product_url)
    for product_id in product_ids:
        contents, _ = get_proxy_results(
            request=request,
            url=content_url % (settings.CONTENTGRAPH_BASE_URL, store_id, product_id))
        for content in contents:
            if not content in results:  # this works because __hash__
                results.append(content)

    return ajax_jsonp({'results': results,
                       'meta': meta})


@append_headers
@check_login
@never_cache
@csrf_exempt
def tag_content(request, store_id, page_id, content_id, product_id=0):
    """Add a API endpoint to the backend for tagging content with products.

    Tag content with a product
    POST /page/:page_id/content/:content_id/tag
    <product-id>
    "Post adds a new tag to the set of existing tags stored in tagged-products."

    List tags
    GET /page/:page_id/content/:content_id/tag
    Tags are all strings.

    Delete a tag
    DELETE /page/:page_id/content/:content_id/tag/<product-id>

    As far as the spec is concerned, product_id is a query parameter
    for the DELETE case, and from content body for the POST case.

    :raises (ValueError, TypeError)
    """
    store_content_url = '{url}/store/{store_id}/content/{content_id}'.format(
        url=settings.CONTENTGRAPH_BASE_URL, store_id=store_id,
        content_id=content_id)
    page_content_url = '{url}/store/{store_id}/page/{page_id}/content/{content_id}'.format(
        url=settings.CONTENTGRAPH_BASE_URL, store_id=store_id, page_id=page_id,
        content_id=content_id)

    # get the content (it's a json string)
    resp, cont = get_proxy_results(request=request, url=store_content_url,
                                   raw=True, method='GET')
    content = json.loads(cont)  # raises ValueError here if fetching failed

    if request.method == 'GET':
        # return the list of tags on this product
        return ajax_jsonp({
            'results': content.get('tagged-products', [])
        })

    tagged_products = content.get('tagged-products', [])  # :type list
    if not product_id:
        product_id = (request.body or '')

    # add one tag to the list of tags (if it doesn't already exist)
    if request.method == 'POST':
        if not str(product_id) in tagged_products:
            tagged_products.append(str(product_id))
            # new product not in list? patch the content with new list
            resp, cont = get_proxy_results(request=request, url=store_content_url,
                body=json.dumps({"tagged-products": tagged_products}),
                method='PATCH', raw=True)

            # return an ajax response instead of just the text
            return ajax_jsonp(result=json.loads(cont), status=resp.status)

        else:  # already in the list
            return HttpResponse(status=200)

    # remove one tag from the list of tags
    if product_id and request.method == 'DELETE':
        if not str(product_id) in tagged_products:
            return HttpResponse(status=200)  # already out of the list

        tagged_products.remove(str(product_id))
        # new product in list? patch the content with new list
        resp, cont = get_proxy_results(request=request, url=store_content_url,
            body=json.dumps({"tagged-products": tagged_products}),
            method='PATCH', raw=True)

        # return an ajax response instead of just the text
        return ajax_jsonp(result=json.loads(cont), status=resp.status)

    return HttpResponseBadRequest()  # missing something (say, product id)
