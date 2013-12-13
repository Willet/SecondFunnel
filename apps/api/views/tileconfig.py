import json
import itertools

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from apps.api.decorators import check_login, request_methods

from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def prioritize_tile(request, store_id, page_id, tileconfig_id):
    # DEFER: may need to mark TileConfig as 'stale'
    payload = json.dumps({'prioritized': 'true'})

    r = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).PATCH(data=payload)

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

    r = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).PATCH(data=payload)

    response = HttpResponse(content=r.content, status=r.status_code)
    return mimic_response(r, response)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_tile_configs(request, store_id, page_id):
    r = ContentGraphClient.page(page_id)('tile-config').GET(params=request.GET)
    response = HttpResponse(content=r.content, status=r.status_code)
    if r.status_code == 200:
        tiles_json = r.json()
        tiles_json['results'] = expand_tile_configs(store_id, tiles_json['results'])
        response = HttpResponse(content=json.dumps(tiles_json), status=r.status_code)
    return mimic_response(r, response)


def expand_products(store_id, page_id, products):

    def get_product_tiles(store_id, product_id):
        params = {'product-ids': product_id}  # DEFER: , 'template': 'product'}
        tiles = []
        while True:
            r = ContentGraphClient.page(page_id)('tile-config').GET(params=params)
            result_json = r.json()
            tiles += result_json['results']

            # fetch all the results
            if 'meta' in result_json and 'cursors' in result_json['meta'] and 'next' in result_json['meta']['cursors']:
                params['offset'] = result_json['meta']['cursors']['next']
            else:
                break
        return tiles

    # flatten lists
    content_ids = list(itertools.chain.from_iterable([record['image-ids'] for record in products]))
    content_ids += [record['default-image-id'] for record in products]
    content_list = ContentGraphClient.store(store_id).content().GET(params={'ids': content_ids}).json.results
    content_set = {}
    for content in content_list:
        content_set[content['id']] = content

    for record in products:
        record['tile-configs'] = get_product_tiles(store_id, record['id'])
        if 'default-image-id' in record:
            record['default-image'] = content_set[record['default-image-id']]
        if 'image-ids' in record:
            record['images'] = [content_set[content_id] for content_id in record['image-ids']]

    return products


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

    response = HttpResponse(content=r.content, status=r.status_code)
    if r.status_code == 200:
        result_json = r.json()
        # get related tiles if they exist
        result_json['results'] = expand_products(store_id, page_id, result_json['results'])
        response = HttpResponse(content=json.dumps(result_json), status=r.status_code)
    return mimic_response(r, response)


def expand_contents(store_id, page_id, contents):

    def get_content_tiles(store_id, content_id):
        params = {'content-ids': content_id}
        tiles = []
        while True:
            r = ContentGraphClient.page(page_id)('tile-config').GET(params=params)
            result_json = r.json()
            tiles += result_json['results']

            # fetch all the results
            if 'meta' in result_json and 'cursors' in result_json['meta'] and 'next' in result_json['meta']['cursors']:
                params['offset'] = result_json['meta']['cursors']['next']
            else:
                break
        return tiles

    for record in contents:
        record['tile-configs'] = get_content_tiles(store_id, record['id'])

    return contents


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
            r = ContentGraphClient.page(page_id)('tile-config').GET(params=params)
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
        result_json['results'] = expand_contents(store_id, page_id, result_json['results'])
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
    r = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).GET()
    response = HttpResponse(content=r.content, status=r.status_code)
    if r.status_code == 200:
        record = expand_tile_config(store_id, r.json())
        response = HttpResponse(content=json.dumps(record), status=r.status_code)
    return mimic_response(r, response)


def expand_tile_config(store_id, record):
    records = expand_tile_configs(store_id, [record])
    return records[0]


def expand_tile_configs(store_id, configs):
    # TODO: this assumes multi-id lookups always return all results
    #       I think... this is a valid assumption, I am not certain at this point in time

    product_ids = list(itertools.chain.from_iterable([config['product-ids'] for config in configs]))
    product_list = ContentGraphClient.store(store_id).product().GET(params={'ids': product_ids}).json.results
    product_set = {}
    for product in product_list:
        product_set[product['id']] = product

    content_ids = list(itertools.chain.from_iterable([config['content-ids'] for config in configs]))
    content_list = ContentGraphClient.store(store_id).content().GET(params={'ids': content_ids}).json.results
    content_set = {}
    for content in content_list:
        content_set[content['id']] = content

    for record in configs:
        # convert product ids to json representation
        if 'product-ids' in record:
            record['products'] = [product_set[product_id] for product_id in record['product-ids']]
        # convert contents ids to json representation
        if 'content-ids' in record:
            record['content'] = [content_set[content_id] for content_id in record['content-ids']]

    return configs


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
    r = ContentGraphClient.page(page_id)('tile-config').POST(data=payload)
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
    r = ContentGraphClient.page(page_id)('tile-config').POST(data=payload)
    response = HttpResponse(content=r.content, status=r.status_code)
    return mimic_response(r, response)
