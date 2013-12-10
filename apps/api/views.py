import httplib2
import json

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseNotAllowed)
from django.conf import settings

from apps.api.decorators import check_login, append_headers, request_methods
from apps.api.tasks import fetch_queue
from apps.intentrank.utils import ajax_jsonp

from resources import ContentGraphClient
from utils import mimic_response


# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view
def proxy_request(path, verb='GET', query_string=None, body=None, headers=None):
    if not headers:
        headers = {}

    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)

    if query_string:
        url += '?' + query_string

    if not headers.get('ApiKey', None):
        headers['ApiKey'] = 'secretword'

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=verb,
        body=body,
        headers=headers
    )

    return HttpResponse(
        content=content,
        status=int(response['status']),
        content_type=response['content-type']
    )


def content_request(content_url, method='GET'):
    response = proxy_request(
        content_url,
        verb=method
    )

    if not (200 <= response.status_code < 300):
        response.status_code = 500

    return response


def tile_config_request(url, object_id, object_type='product',
                        method='POST', data=None):
    """By default (POST), creates a tile config for a product, or
    a piece of content.
    """

    object_template = object_type  # i.e. products use the product template
    if object_type == 'content':
        object_template = 'image'  # but content uses the image template

    response = proxy_request(
        url,
        verb=method,
        body=json.dumps({
            'template': data.get('template', object_template),
            '%s-ids' % object_type: [object_id]
        })
    )

    # Should we do some amalgamated response?
    # I don't think the response is used, so just return for now
    if not (200 <= response.status_code < 300):
        response.status_code = 500

    return response


def tile_request(url, method='POST', data=None):
    """By default, POSTs a tile to the page's tile url.

    :param data the json tile as a string.
    :type data str
    """

    response = proxy_request(
        url,
        verb=method,
        body=data
    )

    # Should we do some amalgamated response?
    # I don't think the response is used, so just return for now
    if not (200 <= response.status_code < 300):
        response.status_code = 500

    return response


def get_proxy_results(request, url, body=None, raw=False, method=None):
    """small wrapper around all api requests to content graph.

    :param raw if True, returns the entire http tuple.
    :type raw bool

    :param method if given, overrides the one in request.
    :type method str

    :returns tuple
    :raises (ValueError, IndexError)
    """
    h = httplib2.Http()
    response, content = h.request(uri=url, method=method or request.method,
        body=body, headers=request.NEW_HEADERS or request.META)

    if raw:
        return (response, content)

    resp_obj = json.loads(content)
    return (resp_obj['results'], resp_obj['meta'])


@append_headers
@check_login
@never_cache
@csrf_exempt
def proxy_view(request, path):
    """Nick is not a security expert.

    He does, however, recommend we read up security policy to see if using
    CORS is sufficient to prevent against CSRF, because he is having a hard
    time handling that...
    """

    target_url = settings.CONTENTGRAPH_BASE_URL

    url = '%s/%s' % (target_url, path)
    if request.META.get('QUERY_STRING', False):
        url += '?' + request.META['QUERY_STRING']

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=request.method,
        body=request.body or None,
        headers=request.NEW_HEADERS
    )

    return HttpResponse(
        content=content,
        status=response['status'],
        content_type=response['content-type']
    )


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

    tagged_products = content.get('tagged-products', []) # :type list
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


# login_required decorator?
@never_cache
@csrf_exempt
@request_methods('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH')
def proxy_tile(request, store_id, page_id, object_type='product', object_id=''):
    """generates or deletes tiles and tileconfigs for either the
    product or content that is being passed into this function.
    """

    # not the complete http verb list -- just the ones we know for sure
    # we support.
    allowed_object_types = ['product', 'content']

    if not request.user or not request.user.is_authenticated():
        return HttpResponse(
            content='{"error": "Not logged in"}',
            mimetype='application/json',
            status=401
        )

    if not object_id or not object_type in allowed_object_types:
        # we only support product or content right now, and it requires an id
        return HttpResponseBadRequest()

    request_body = json.loads(request.body or '{}')

    object_url = 'store/{store_id}' \
                 '/page/{page_id}' \
                 '/{object_type}/{object_id}'.format(
        store_id=store_id,
        page_id=page_id,
        object_type=object_type,
        object_id=object_id)

    tile_config_url = 'page/{page_id}/tile-config'.format(
        page_id=page_id,
    )

    tile_url = 'page/{page_id}/tile'.format(
        page_id=page_id,
    )

    response = content_request(object_url, method=request.method)

    # could not get the object itself.
    if response.status_code == 500:
        return response

    if request.method == 'PUT':
        request.method = 'POST'  # tileconfig doesn't accept PUTs right now

    # create corresponding tile config
    response = tile_config_request(url=tile_config_url,
        object_type=object_type, object_id=object_id,
        method=request.method, data=request_body)

    # could not (verb|create) a tile config for this object.
    if response.status_code == 500:
        return response

    # tileconfig request returns a tile. create corresponding tile
    response = tile_request(url=tile_url,
        method=request.method, data=response.content)

    return response


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


@request_methods('DELETE')
@check_login
@never_cache
@csrf_exempt
def delete_scraper(request, store_id, scraper_name):
    r = ContentGraphClient.scraper.store(store_id, scraper_name).DELETE()

    response = HttpResponse(content=r.content, status=r.status_code)

    return mimic_response(r, response)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_scrapers(request, store_id):
    r = ContentGraphClient.scraper.store(store_id).GET()

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

        r = ContentGraphClient.store(store_id).page(page_id).content(content_id).PUT('')

        if r.status_code != 200:
            return HttpResponse(status=500)

    return HttpResponse()


@check_login
def check_queue(request, queue_name):
    """Provides a URL to instantly poll an SQS queue, and, if a message is
    found, process it.
    """
    queue = None

    def get_default_queue_by_name(name, region=settings.AWS_SQS_REGION_NAME):
        """maybe this should be somewhere else if it is useful."""
        queues = settings.AWS_SQS_POLLING_QUEUES
        for queue in queues:
            if queue.get('region_name', None):
                if queue['region_name'] != region:
                    continue
            if queue.get('queue_name', None):
                if queue['queue_name'] != name:
                    continue
            if queue:
                return queue
        raise ValueError('Queue by that name ({0}) is missing'.format(name))

    try:
        queue = get_default_queue_by_name(queue_name)
        return ajax_jsonp(fetch_queue(queue))
    except (AttributeError, ValueError) as err:
        # no queue or none queue
        return ajax_jsonp({err.__class__.__name__: err.message})


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def prioritize_tile(request, store_id, page_id, tileconfig_id):
    # DEFER: may need to issue something due to the change?
    # e.g. update generated tiles for this tile-config
    payload = json.dumps({'prioritized': 'true'})

    r = ContentGraphClient.page(page_id).__getattr__('tile-config')(tileconfig_id).PATCH(data=payload)

    response = HttpResponse(content=r.content, status=r.status_code)
    return mimic_response(r, response)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def deprioritize_tile(request, store_id, page_id, tileconfig_id):
    # DEFER: may need to issue something due to the change?
    # e.g. update generated tiles for this tile-config
    payload = json.dumps({'prioritized': 'false'})

    r = ContentGraphClient.page(page_id).__getattr__('tile-config')(tileconfig_id).PATCH(data=payload)

    response = HttpResponse(content=r.content, status=r.status_code)
    return mimic_response(r, response)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_tile_configs(request, store_id, page_id):
    r = ContentGraphClient.page(page_id).__getattr__('tile-config').GET(params=request.GET)

    def get_content(store_id, content_id):
        try:
            return ContentGraphClient.store(store_id).content(content_id).GET().json()
        except:
            return None

    def get_product(store_id, product_id):
        try:
            record = ContentGraphClient.store(store_id).product(product_id).GET().json()
            if 'default-image-id' in record:
                record['default-image'] = get_content(store_id, record['default-image-id'])
            return record
        except:
            return None

    # DEFER PERF: these lookups could be made in parallel, and merged back in after
    response = HttpResponse(content=r.content, status=r.status_code)
    if r.status_code == 200:
        tiles_json = r.json()
        for record in tiles_json['results']:
            # convert product ids to json reporesentations
            if 'product-ids' in record:
                record['products'] = [get_product(store_id, product_id) for product_id in record['product-ids']]
            # convert contents ids to json reporesentations
            if 'content-ids' in record:
                record['content'] = [get_content(store_id, content_id) for content_id in record['content-ids']]
        response = HttpResponse(content=json.dumps(tiles_json), status=r.status_code)
    return mimic_response(r, response)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_all_products(request, store_id, page_id):
    r = ContentGraphClient.store(store_id).product().GET(params=request.GET)

    def get_content(store_id, content_id):
        try:
            return ContentGraphClient.store(store_id).content(content_id).GET().json()
        except:
            return None

    def get_product_tiles(store_id, product_id):
        params = {'product-ids': product_id}  # DEFER: , 'template': 'product'}
        tiles = []
        while True:
            r = ContentGraphClient.page(page_id).__getattr__('tile-config').GET(params=params)
            result_json = r.json()
            tiles += result_json['results']

            # fetch all the results
            if 'meta' in result_json and 'cursors' in result_json['meta'] and 'next' in result_json['meta']['cursors']:
                params['offset'] = result_json['meta']['cursors']['next']
            else:
                break
        return tiles

    response = HttpResponse(content=r.content, status=r.status_code)
    if r.status_code == 200:
        result_json = r.json()
        # get related tiles if they exist
        for record in result_json['results']:
            record['tile-configs'] = get_product_tiles(store_id, record['id'])
            if 'default-image-id' in record:
                record['default-image'] = get_content(store_id, record['default-image-id'])
            if 'image-ids' in record:
                record['images'] = [get_content(store_id, content_id) for content_id in record['image-ids']]

        response = HttpResponse(content=json.dumps(result_json), status=r.status_code)
    return mimic_response(r, response)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_all_content(request, store_id, page_id):
    r = ContentGraphClient.store(store_id).content().GET(params=request.GET)

    def get_product(store_id, product_id):
        try:
            return ContentGraphClient.store(store_id).product(product_id).GET().json()
        except:
            return None

    def get_content_tiles(store_id, content_id):
        params = {'content-ids': content_id}  # DEFER: , 'template': 'product'}
        tiles = []
        while True:
            r = ContentGraphClient.page(page_id).__getattr__('tile-config').GET(params=params)
            result_json = r.json()
            tiles += result_json['results']

            # fetch all the results
            if 'meta' in result_json and 'cursors' in result_json['meta'] and 'next' in result_json['meta']['cursors']:
                params['offset'] = result_json['meta']['cursors']['next']
            else:
                break
        return tiles

    response = HttpResponse(content=r.content, status=r.status_code)
    if r.status_code == 200:
        result_json = r.json()
        # get related tiles if they exist
        for record in result_json['results']:
            record['tile-configs'] = get_content_tiles(store_id, record['id'])
            if 'tagged-products' in record:
                record['tagged-products'] = [get_product(store_id, product_id) for product_id in record['tagged-products']]
        response = HttpResponse(content=json.dumps(result_json), status=r.status_code)
    return mimic_response(r, response)


def fetch_products(store_id, product_ids):
    try:
        params = {'ids': product_ids}
        json = ContentGraphClient.store(store_id).product().GET(params=params).json()
        return json
    except:
        return None


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def get_page_tile_config(request, store_id, page_id, tileconfig_id):
    r = ContentGraphClient.page(page_id).__getattr__('tile-config')(tileconfig_id).GET()

    def get_product(store_id, product_id):
        return ContentGraphClient.store(store_id).product(product_id).GET().json()

    def get_content(store_id, content_id):
        return ContentGraphClient.store(store_id).content(content_id).GET().json()

    response = HttpResponse(content=r.content, status=r.status_code)
    if r.status_code == 200:
        record = r.json()
        # convert product ids to json reporesentations
        if 'product-ids' in record:
            record['products'] = [get_product(store_id, product_id) for product_id in record['product-ids']]
        # convert contents ids to json reporesentations
        if 'content-ids' in record:
            record['content'] = [get_content(store_id, content_id) for content_id in record['content-ids']]
        response = HttpResponse(content=json.dumps(record), status=r.status_code)
    return mimic_response(r, response)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def add_product_to_page(request, store_id, page_id, product_id):
    # verify the tile config does not already exist
    tile_check_params = {'template': 'product', 'product-ids': product_id}
    tile_check = ContentGraphClient.page(page_id)('tile-config').POST(params=tile_check_params)
    if tile_check.status_code == 200 and len(tile_check.json.results) != 0:
        # TODO: note this does not handle the case where CONTENT GRAPH returns zero results
        #       even though there is RESULTS to be had...
        # NOTE: search endpoint does not return 404 on NO RESULTS
        response = HttpResponse(content=json.dumps(tile_check.json.results[0]), status=tile_check.status_code)
        return mimic_response(tile_check, response)

    payload = json.dumps({
        'template': 'product',
        'product-ids': [product_id]
        })
    r = ContentGraphClient.page(page_id)('tile-config')().POST(data=payload)
    response = HttpResponse(content=r.content, status=r.status_code)
    return mimic_response(r, response)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def add_content_to_page(request, store_id, page_id, content_id):
    # verify the tile config does not already exist
    tile_check_params = {'template': 'content', 'content-ids': content_id}
    tile_check = ContentGraphClient.page(page_id)('tile-config').POST(params=tile_check_params)
    if tile_check.status_code == 200 and len(tile_check.json.results) != 0:
        # TODO: note this does not handle the case where CONTENT GRAPH returns zero results
        #       even though there is RESULTS to be had...
        # NOTE: search endpoint does not return 404 on NO RESULTS
        response = HttpResponse(content=json.dumps(tile_check.json.results[0]), status=tile_check.status_code)
        return mimic_response(tile_check, response)

    # create the tile config
    payload = json.dumps({
        'template': 'content',
        'content-ids': [content_id]
        })
    r = ContentGraphClient.page(page_id)('tile-config')().POST(data=payload)
    response = HttpResponse(content=r.content, status=r.status_code)
    return mimic_response(r, response)
