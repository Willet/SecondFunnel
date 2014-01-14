import json
import itertools

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from apps.api.decorators import check_login, request_methods

from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response


def cg_response_contains_results(request):
    # TODO: note this does not handle the case where CONTENT GRAPH returns zero results
    #       even though there is RESULTS to be had...
    # NOTE: search endpoint does not return 404 on NO RESULTS
    if request.status_code not in [200, 404]:
        raise ValueError('ContentGraph Error')

    has_no_results = (request.status_code == 404) or (request.status_code == 200 and len(request.json()['results']) == 0)
    return not has_no_results


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def prioritize_tile(request, store_id, page_id, tileconfig_id):
    tileconfig = tileconfig_prioritize(store_id, page_id, tileconfig_id)
    return HttpResponse(content=json.dumps(tileconfig))


def tileconfig_prioritize(store_id, page_id, tileconfig_id):
    payload = json.dumps({
        'prioritized': 'true',
        'stale': 'true'
    })
    r = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).PATCH(data=payload)
    return r.json()


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def deprioritize_tile(request, store_id, page_id, tileconfig_id):
    return mimic_response(tileconfig_deprioritize(store_id, page_id, tileconfig_id))


def tileconfig_deprioritize(store_id, page_id, tileconfig_id):
    payload = json.dumps({
        'prioritized': 'false',
        'stale': 'true'
    })
    return ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).PATCH(data=payload)


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def prioritize_content(request, store_id, page_id, content_id):
    content_prioritize(store_id, page_id, content_id)
    return get_page_content(store_id, page_id, content_id)


def content_prioritize(store_id, page_id, content_id):
    tileconfig = add_content_to_page(store_id, page_id, content_id, prioritized=True)
    if not tileconfig.get('prioritized', 'false') == 'true':
        tileconfig = tileconfig_prioritize(store_id, page_id, tileconfig['id'])
    return tileconfig


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def deprioritize_content(request, store_id, page_id, content_id):
    content_deprioritize(store_id, page_id, content_id)
    return get_page_content(store_id, page_id, content_id)


def content_deprioritize(store_id, page_id, content_id):
    tileconfig = add_content_to_page(store_id, page_id, content_id, prioritized=True)
    if not tileconfig.get('prioritized', 'false') == 'false':
        tileconfig = tileconfig_deprioritize(store_id, page_id, tileconfig['id'])
    return tileconfig


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def prioritize_product(request, store_id, page_id, product_id):
    product_prioritize(store_id, page_id, product_id)
    return get_page_product(store_id, page_id, product_id)


def product_prioritize(store_id, page_id, product_id):
    tileconfig = page_add_product(store_id, page_id, product_id, prioritized=True)
    if not tileconfig.get('prioritized', 'false') == 'true':
        tileconfig = tileconfig_prioritize(store_id, page_id, tileconfig['id'])
    return tileconfig


@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def deprioritize_product(request, store_id, page_id, product_id):
    product_deprioritize(store_id, page_id, product_id)
    return get_page_product(store_id, page_id, product_id)


def product_deprioritize(store_id, page_id, product_id):
    tileconfig = page_add_product(store_id, page_id, product_id, prioritized=True)
    if not tileconfig.get('prioritized', 'false') == 'false':
        tileconfig = tileconfig_deprioritize(store_id, page_id, tileconfig['id'])
    return tileconfig


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


def get_page_content(store_id, page_id, content_id):
    r = ContentGraphClient.store(store_id).content(content_id).GET()
    if r.status_code != 200:
        return HttpResponse(status=r.status_code)
    content = expand_contents(store_id, page_id, [r.json()])[0]
    return HttpResponse(mimetype='application/json', content=json.dumps(content))


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
            content_list = [x for x in content_list if x is not None]
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


def get_page_product(store_id, page_id, product_id):
    r = ContentGraphClient.store(store_id).product(product_id).GET()
    if r.status_code != 200:
        return HttpResponse(status=r.status_code)
    product = expand_products(store_id, page_id, [r.json()])[0]
    return HttpResponse(content=json.dumps(product))


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
            product_list = [x for x in product_list if x is not None]
            product_json = {}
            product_json['meta'] = tiles_json['meta']
            product_json['results'] = product_list
        else:
            product_json = tiles_json
        return mimic_response(r, content=json.dumps(product_json))
    return mimic_response(r)


def tileconfig_to_product(tileconfig):
    if 'products' in tileconfig and len(tileconfig['products']) > 0:
        product = tileconfig['products'][0]
        del tileconfig['products']
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
    content_ids += [record['default-image-id'] for record in products if 'default-image-id' in record]
    content_ids = list(set(content_ids))

    content_list = []
    content_id_sublists = [content_ids[i:i+25] for i in range(0,len(content_ids),25)]
    for content_id_sublist in content_id_sublists:
        content_ids_csv = ",".join([str(x) for x in content_id_sublist])
        content_list.extend(ContentGraphClient.store(store_id).content().GET(params={'id': content_ids_csv}).json()['results'])

    content_set = {}
    for content in content_list:
        content_set[content['id']] = content

    for record in products:
        record['tile-configs'] = get_product_tiles(store_id, record['id'])
        if 'default-image-id' in record:
            if record['default-image-id'] in content_set:
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
    product_ids = list(set(product_ids))
    product_ids_csv = ",".join([str(x) for x in product_ids])
    product_lookup = ContentGraphClient.store(store_id).product().GET(params={'id': product_ids_csv})
    if product_lookup.status_code == 200 and 'results' in product_lookup.json():
        product_list = product_lookup.json()['results']
    else:
        product_list = []

    product_set = {}
    for product in product_list:
        product_set[product['id']] = product

    content_ids = list(itertools.chain.from_iterable([config['content-ids'] for config in configs if 'content-ids' in config]))
    content_ids = list(set(content_ids))
    content_ids_csv = ",".join([str(x) for x in content_ids])
    content_lookup = ContentGraphClient.store(store_id).content().GET(params={'id': content_ids_csv})
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


@request_methods('GET', 'PUT', 'DELETE')
@check_login
@never_cache
@csrf_exempt
def product_operations(request, store_id, page_id, product_id):
    if request.method == 'PUT':
        page_add_product(store_id, page_id, product_id)
    elif request.method == 'DELETE':
        page_remove_product(store_id, page_id, product_id)
    return get_page_product(store_id, page_id, product_id)


def page_add_product(store_id, page_id, product_id, prioritized=False):
    tile_check_params = {'template': 'product', 'product-ids': product_id}
    tile_check = ContentGraphClient.page(page_id)('tile-config').GET(params=tile_check_params)
    if cg_response_contains_results(tile_check):
        return tile_check.json()['results'][0]

    payload = json.dumps({
        'template': 'product',
        'product-ids': [product_id],
        'prioritized': prioritized,
        'stale': 'true'
    })
    r = ContentGraphClient.page(page_id)('tile-config').POST(data=payload)
    return r.json()


def page_remove_product(store_id, page_id, product_id):
    tile_check_params = {'template': 'product', 'product-ids': product_id}
    tile_check = ContentGraphClient.page(page_id)('tile-config').GET(params=tile_check_params)
    if cg_response_contains_results(tile_check):
        tile_id = tile_check.json()['results'][0]['id']
        tile_delete = ContentGraphClient.page(page_id)('tile-config')(tile_id).DELETE()
        mark_page_for_regeneration(store_id, page_id)
        return mimic_response(tile_delete)
    else:
        return HttpResponse(status=200)


@request_methods('GET', 'PUT', 'DELETE')
@check_login
@never_cache
@csrf_exempt
def content_operations(request, store_id, page_id, content_id):
    try:
        if request.method == 'PUT':
            add_content_to_page(store_id, page_id, content_id)
        elif request.method == 'DELETE':
            remove_content_from_page(store_id, page_id, content_id)
    except ValueError:
        return HttpResponse(status=500)
    return get_page_content(store_id, page_id, content_id)


def add_content_to_page(store_id, page_id, content_id, prioritized=False):
    # verify the tile config does not already exist
    tileconfig_params = {'template': 'image', 'content-ids': content_id}
    tileconfigs = ContentGraphClient.page(page_id)('tile-config').GET(params=tileconfig_params)
    if cg_response_contains_results(tileconfigs):
        tileconfig = tileconfigs.json()['results'][0]
        return tileconfig

    # create the tile config
    payload = json.dumps({
        'template': 'image',
        'content-ids': [content_id],
        'prioritized': prioritized,
        'stale': 'true'
    })
    r = ContentGraphClient.page(page_id)('tile-config').POST(data=payload)
    if r.status_code != 200:
        raise ValueError('ContentGraph Error')

    return r.json()


def remove_content_from_page(store_id, page_id, content_id):
    # verify the tile config does not already exist
    tileconfig_params = {'template': 'image', 'content-ids': content_id}
    tileconfigs = ContentGraphClient.page(page_id)('tile-config').GET(params=tileconfig_params)
    if cg_response_contains_results(tileconfigs):
        tileconfig_id = tileconfigs.json()['results'][0]['id']
        delete_tileconfig_request = ContentGraphClient.page(page_id)('tile-config')(tileconfig_id).DELETE()
        mark_page_for_regeneration(store_id, page_id)
        return delete_tileconfig_request.status_code == 200
    else:
        return True


def mark_page_for_regeneration(store_id, page_id):
    """marks a page for regeneration.  When one of the periodic tasks see that
    this page has been marked for regeneration, it will queue up irconfig fot
    this page."""
    attempts = 0 # In the event of a race condition
    while attempts < 50:
        page = ContentGraphClient.store(store_id).page(page_id).GET().json()
        payload = json.dumps({
            'ir-stale': 'true',
            'consistent': 'true',
            'version': page['last-modified']
        })
        r = ContentGraphClient.store(store_id).page(page_id).PATCH(data=payload)
        if r.status_code == 200:
            break
        attempts += 1
