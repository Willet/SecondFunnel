import json
from urllib import urlencode

from django.http import HttpResponse
from django.template import Context, Template
import httplib2
from apps.assets.models import Product

# All requests are get requests at the moment
# URL to IntentRank looks something like this:
# /intentrank/intentrank/store/<STORE SLUG>/page/<PAGE ID>/<FUNCTION>

# getseeds?seeds=1,2,3,4&results=2
from apps.pinpoint.models import Campaign

SUCCESS         = 200
BAD_REQUEST     = 400
DEFAULT_RESULTS = 12

def process_intentrank_request(request, store, page, function_name,
                               param_dict):
    url = 'http://URL/store/{0}/page/{1}/{2}'.format(store, page, function_name)
    params   = urlencode(param_dict)

    headers = {}
    cookie = request.session.get('ir-cookie')
    if cookie:
        headers['Cookie'] = cookie

    h = httplib2.Http()
    try:
        response, content = h.request(
            url,
            'GET',
            headers=headers,
            body=params
        )
    except Exception: # TODO: Replace with more specific error
        return Product.objects.all(), SUCCESS # TODO: Replace with error again

    if response.get('set-cookie'):
        request.session['ir-cookie'] = response['set-cookie']

    try:
        results = json.loads(content)
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

    products, status = process_intentrank_request(
        request, store, page, 'getseeds', {
        'seeds'  : seeds,
        'results': results
        }
    )

    result = products_to_template(products, page)

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)

def get_results(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    results = request.GET.get('results', DEFAULT_RESULTS)

    products, status = process_intentrank_request(
        request, store, page, 'getresults', {
            'results': results
        }
    )

    result = products_to_template(products, page)

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)

def update_clickstream(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    product_id = request.GET.get('product_id')

    _, status = process_intentrank_request(request, store, page, 'getseeds', {
        'product_id': product_id
    })

    # Return JSON results
    return HttpResponse("[]", mimetype='application/json', status=status)