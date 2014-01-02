import json
import itertools

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from apps.api.decorators import check_login, request_methods

from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response


def is_empty(request):
    # TODO: note this does not handle the case where CONTENT GRAPH returns zero results
    #       even though there is RESULTS to be had...
    # NOTE: search endpoint does not return 404 on NO RESULTS
    return (request.status_code == 404) or (request.status_code == 200 and len(request.json()['results']) == 0)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def prioritize_tile(request, store_id, page_id, tileconfig_id):
    # DEFER: may need to mark TileConfig as 'stale'
    payload = json.dumps({'prioritized': 'true'})

    r = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).PATCH(data=payload)

    return mimic_response(r)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def deprioritize_tile(request, store_id, page_id, tileconfig_id):
    # DEFER: may need to issue something due to the change?
    # e.g. update generated tiles for this tile-config
    payload = json.dumps({'prioritized': 'false'})

    r = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).PATCH(data=payload)

    return mimic_response(r)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_tile_configs(request, store_id, page_id):
    r = ContentGraphClient.page(page_id)('tile-config').GET(params=request.GET)
    if r.status_code == 200:
        tiles_json = r.json()
        if 'results' in tiles_json:
            tiles_json['results'] = expand_tile_configs(store_id, tiles_json['results'])
        return mimic_response(r, content=json.dumps(tiles_json))
    return mimic_response(r)


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_content(request, store_id, page_id):
    params = request.GET.dict()
    params['template'] = 'image'
    r = ContentGraphClient.page(page_id)('tile-config').GET(params=params)
    if r.status_code == 200:
        tiles_json = r.json()
        if 'results' in tiles_json:
            tiles_json['results'] = expand_tile_configs(store_id, tiles_json['results'])
            content_list = [tileconfig_to_content(x) for x in tiles_json['results']]
            content_json = {}
            content_json['meta'] = tiles_json['meta']
            content_json['results'] = content_list
        else:
            content_json = tiles_json
        return mimic_response(r, content=json.dumps(content_json))
    return mimic_response(r)


def tileconfig_to_content(tileconfig):
    if 'content' in tileconfig and len(tileconfig['content']) > 0:
        content = tileconfig['content'][0]
        del tileconfig['content']
        content['tile-configs'] = [tileconfig]
        return content
    else:
        return None


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_products(request, store_id, page_id):
    params = request.GET.dict()
    params['template'] = 'product'
    r = ContentGraphClient.page(page_id)('tile-config').GET(params=params)
    if r.status_code == 200:
        tiles_json = r.json()
        if 'results' in tiles_json:
            tiles_json['results'] = expand_tile_configs(store_id, tiles_json['results'])
            product_list = [tileconfig_to_product(x) for x in tiles_json['results']]
            product_json = {}
            product_json['meta'] = tiles_json['meta']
            product_json['results'] = product_list
        else:
            product_json = tiles_json
        return mimic_response(r, content=json.dumps(product_json))
    return mimic_response(r)


def tileconfig_to_product(tileconfig):
    if 'product' in tileconfig and len(tileconfig['product']) > 0:
        product = tileconfig['product'][0]
        del tileconfig['product']
        product['tile-configs'] = [tileconfig]
        return product
    else:
        return None


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
    content_ids = list(itertools.chain.from_iterable([record['image-ids'] for record in products if 'image-ids' in record]))
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
            record['images'] = [content_set[content_id] for content_id in record['image-ids'] if content_id in content_set]

    return products


@request_methods('GET')
@check_login
@never_cache
@csrf_exempt
def list_page_all_products(request, store_id, page_id):
    r = ContentGraphClient.store(store_id).product().GET(params=request.GET)

    if r.status_code == 200:
        result_json = r.json()
        result_json['results'] = expand_products(store_id, page_id, result_json['results'])
        return mimic_response(r, content=json.dumps(result_json))
    return mimic_response(r)


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
        params = {'content-ids': content_id}  # DEFER: , 'template': 'image'}
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

    if r.status_code == 200:
        result_json = r.json()
        # get related tiles if they exist
        result_json['results'] = expand_contents(store_id, page_id, result_json['results'])
        return mimic_response(r, content=json.dumps(result_json))
    return mimic_response(r)


def expand_contents(store_id, page_id, contents):

    def get_content_tiles(store_id, content_id):
        params = {'content-ids': content_id}
        tiles = []
        while True:
            r = ContentGraphClient.page(page_id)('tile-config').GET(params=params)
            result_json = r.json()
            if 'results' in result_json:
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
def get_page_tile_config(request, store_id, page_id, tileconfig_id):
    r = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).GET()
    if r.status_code == 200:
        record = expand_tile_config(store_id, r.json())
        return mimic_response(r, content=json.dumps(record))
    return mimic_response(r)


def expand_tile_config(store_id, record):
    records = expand_tile_configs(store_id, [record])
    return records[0]


def expand_tile_configs(store_id, configs):
    # TODO: this assumes multi-id lookups always return all results
    #       I think... this is a valid assumption, I am not certain at this point in time

    product_ids = list(itertools.chain.from_iterable([config['product-ids'] for config in configs if 'product-ids' in config]))
    product_lookup = ContentGraphClient.store(store_id).product().GET(params={'ids': product_ids})
    if product_lookup.status_code == 200 and 'results' in product_lookup.json():
        product_list = product_lookup.json()['results']
    else:
        product_list = []

    product_set = {}
    for product in product_list:
        product_set[product['id']] = product

    content_ids = list(itertools.chain.from_iterable([config['content-ids'] for config in configs if 'content-ids' in config]))
    content_lookup = ContentGraphClient.store(store_id).content().GET(params={'ids': content_ids})
    if content_lookup.status_code == 200 and 'results' in content_lookup.json():
        content_list = content_lookup.json()['results']
    else:
        content_list = []
    content_set = {}
    for content in content_list:
        content_set[content['id']] = content

    for record in configs:
        # convert product ids to json representation
        if 'product-ids' in record:
            record['products'] = [product_set[product_id] for product_id in record['product-ids'] if product_id in product_set]
        # convert contents ids to json representation
        if 'content-ids' in record:
            record['content'] = [content_set[content_id] for content_id in record['content-ids'] if content_id in content_set]

    return configs


@request_methods('PUT', 'DELETE')
@check_login
@never_cache
@csrf_exempt
def add_remove_product_from_page(request, store_id, page_id, product_id):
    if request.method == 'PUT':
        return add_product_to_page(request, store_id, page_id, product_id)
    else:
        return remove_product_from_page(request, store_id, page_id, product_id)


@request_methods('PUT')
def add_product_to_page(request, store_id, page_id, product_id):
    tile_check_params = {'template': 'product', 'product-ids': product_id}
    tile_check = ContentGraphClient.page(page_id)('tile-config').GET(params=tile_check_params)
    if not is_empty(tile_check):
        return mimic_response(tile_check, content=json.dumps(tile_check.json()['results'][0]))

    payload = json.dumps({
        'template': 'product',
        'product-ids': [product_id]
        })
    r = ContentGraphClient.page(page_id)('tile-config').POST(data=payload)
    return mimic_response(r)


@request_methods('DELETE')
def remove_product_from_page(request, store_id, page_id, product_id):
    tile_check_params = {'template': 'product', 'product-ids': product_id}
    tile_check = ContentGraphClient.page(page_id)('tile-config').GET(params=tile_check_params)
    if not is_empty(tile_check):
        tile_id = tile_check.json()['results'][0]['id']
        tile_delete = ContentGraphClient.page(page_id)('tile-config')(tile_id).DELETE()
        return mimic_response(tile_delete)
    else:
        return HttpResponse(status=200)


@request_methods('PUT', 'DELETE')
@check_login
@never_cache
@csrf_exempt
def add_remove_content_from_page(request, store_id, page_id, content_id):
    if request.method == 'PUT':
        return add_content_to_page(request, store_id, page_id, content_id)
    else:
        return remove_content_from_page(request, store_id, page_id, content_id)


@request_methods('PUT')
def add_content_to_page(request, store_id, page_id, content_id):
    # verify the tile config does not already exist
    tileconfig_params = {'template': 'image', 'content-ids': content_id}
    tileconfigs = ContentGraphClient.page(page_id)('tile-config').GET(params=tileconfig_params)
    if not is_empty(tileconfigs):
        return mimic_response(tileconfigs, content=json.dumps(tileconfigs.json()['results'][0]))

    # create the tile config
    payload = json.dumps({
        'template': 'image',
        'content-ids': [content_id]
        })
    r = ContentGraphClient.page(page_id)('tile-config').POST(data=payload)
    return mimic_response(r)


@request_methods('DELETE')
def remove_content_from_page(request, store_id, page_id, content_id):
    # verify the tile config does not already exist
    tileconfig_params = {'template': 'image', 'content-ids': content_id}
    tileconfigs = ContentGraphClient.page(page_id)('tile-config').GET(params=tileconfig_params)
    if not is_empty(tileconfigs):
        tileconfig_id = tileconfigs.json()['results'][0]['id']
        delete_tileconfig_request = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).DELETE()
        return mimic_response(delete_tileconfig_request)
    else:
        return HttpResponse(status=200)
