import contextlib
import json
from urllib2 import urlopen, URLError
from urllib import urlencode

from django.core import serializers
from django.http import HttpResponse
from apps.assets.models import Product

# All requests are get requests at the moment
# URL to IntentRank looks something like this:
# /intentrank/intentrank/store/<STORE SLUG>/page/<PAGE ID>/<FUNCTION>

# getseeds?seeds=1,2,3,4&results=2


SUCCESS         = 200
BAD_REQUEST     = 400
DEFAULT_RESULTS = 12

def process_intentrank_request(store, page, function_name, param_dict):
    base_url = '{0}{1}'.format(store, page)
    params   = urlencode(param_dict)
    url      = '{0}/{1}?{2}'.format(base_url, function_name, params)

    try:
        with contextlib.closing(urlopen(url)) as file:
            json_str = file.read()
    except (URLError, ValueError):
        return [], BAD_REQUEST

    try:
        results = json.loads(json_str)
    except ValueError:
        return [], BAD_REQUEST

    products = Product.objects.filter(pk__in=results.get('products'))
    return products, SUCCESS

def get_seeds(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    seeds   = request.GET.get('seeds', '-1')
    results = request.GET.get('results', DEFAULT_RESULTS)

    products, status = process_intentrank_request(store, page, 'getseeds', {
        'seeds'  : seeds,
        'results': results
    })
    result = serializers.serialize('json', products)

    return HttpResponse(result, mimetype='application/json', status=status)

def get_results(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    results = request.GET.get('results', DEFAULT_RESULTS)

    products, status = process_intentrank_request(store, page, 'getresults', {
        'results': results
    })
    result = serializers.serialize('json', products)

    # Return JSON results
    return HttpResponse(result, mimetype='application/json', status=status)

def update_clickstream(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    product_id = request.GET.get('product_id')

    _, status = process_intentrank_request(store, page, 'getseeds', {
        'product_id': product_id
    })

    # Return JSON results
    return HttpResponse("{}", mimetype='application/json', status=status)