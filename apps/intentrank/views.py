import contextlib
import json
from urllib2 import urlopen, URLError
from urllib import urlencode

from django.core import serializers
from django.http import HttpResponse
from django.template import Context, Template
from apps.assets.models import Product

# All requests are get requests at the moment
# URL to IntentRank looks something like this:
# /intentrank/intentrank/store/<STORE SLUG>/page/<PAGE ID>/<FUNCTION>

# getseeds?seeds=1,2,3,4&results=2
from apps.pinpoint.models import Campaign

SUCCESS         = 200
BAD_REQUEST     = 400
DEFAULT_RESULTS = 12

def process_intentrank_request(store, page, function_name, param_dict):
    base_url = 'http://URL/store/{0}/page/{1}'.format(store, page)
    params   = urlencode(param_dict)
    url      = '{0}/{1}?{2}'.format(base_url, function_name, params)

    try:
        with contextlib.closing(urlopen(url)) as file:
            json_str = file.read()
    except (URLError, ValueError):
        return Product.objects.all(), SUCCESS

    try:
        results = json.loads(json_str)
    except ValueError:
        return [], BAD_REQUEST

    products = Product.objects.filter(pk__in=results.get('products'))
    return products, SUCCESS

# TODO: We shouldn't be doing this on the backend
# Might make more sense to just use JS templates on the front end for
# consistency
def products_to_template(products, campaign_id):
    # Get theme
    campaign = Campaign.objects.get(pk=campaign_id)
    theme    = campaign.store.theme
    discovery_theme = "".join([
        "{% load pinpoint_ui %}",
        "<div class='block product' {{product.data|safe}}>",
        theme.discovery_product,
        "</div>"
    ])

    results = []

    for product in products:
        context = Context()
        context.update({
            'product': product
        })
        results.append(Template(discovery_theme).render(context))

    return results

def get_seeds(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    seeds   = request.GET.get('seeds', '-1')
    results = request.GET.get('results', DEFAULT_RESULTS)

    products, status = process_intentrank_request(store, page, 'getseeds', {
        'seeds'  : seeds,
        'results': results
    })

    result = products_to_template(products, page)

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)

def get_results(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    results = request.GET.get('results', DEFAULT_RESULTS)

    products, status = process_intentrank_request(store, page, 'getresults', {
        'results': results
    })

    result = products_to_template(products, page)

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)

def update_clickstream(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    product_id = request.GET.get('product_id')

    _, status = process_intentrank_request(store, page, 'getseeds', {
        'product_id': product_id
    })

    # Return JSON results
    return HttpResponse("[]", mimetype='application/json', status=status)