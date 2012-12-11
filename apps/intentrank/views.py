import json
from urllib import urlencode

from django.http import HttpResponse
from django.template import Context, Template
import httplib2
from apps.assets.models import Product, Store
from django.conf import settings

# All requests are get requests at the moment
# URL to IntentRank looks something like this:
# /intentrank/intentrank/store/<STORE SLUG>/page/<PAGE ID>/<FUNCTION>

# getseeds?seeds=1,2,3,4&results=2
from apps.pinpoint.models import Campaign
from secondfunnel.settings.common import INTENTRANK_BASE_URL

SUCCESS          = 200
BAD_REQUEST      = 400
DEFAULT_RESULTS  = 12
ALLOWED_STATUSES = [SUCCESS]

def random_products(store, param_dict):
    store_id = Store.objects.get(slug__exact=store)
    num_results = param_dict.get('results', DEFAULT_RESULTS)
    results = Product.objects.filter(store_id__exact=store_id).order_by('?')
    return results[:num_results]

def send_intentrank_request(request, url, method='GET', headers=None):
    if not headers:
        headers = {}

    cookie = request.session.get('ir-cookie')
    if cookie:
        headers['Cookie'] = cookie

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=method,
        headers=headers,
    )

    if response.get('set-cookie'):
        request.session['ir-cookie'] = response['set-cookie']

    return response, content

def process_intentrank_request(request, store, page, function_name,
                               param_dict):

    url = '{0}/intentrank/store/{1}/page/{2}/{3}'.format(
        INTENTRANK_BASE_URL, store, page, function_name)
    params   = urlencode(param_dict)
    url = '{0}?{1}'.format(url, params)

    if settings.DEBUG:
        return random_products(store, param_dict), SUCCESS

    try:
        response, content = send_intentrank_request(request, url)
    except Exception: # TODO: Replace with more specific error
        # TODO: Replace with error; for use until IR is running
        return random_products(store, param_dict), SUCCESS

    if not response.status in ALLOWED_STATUSES:
        # TODO: Replace with error; for use until IR is running
        return random_products(store, param_dict), SUCCESS

    try:
        results = json.loads(content)
    except ValueError:
        # TODO: Replace with error; for use until IR is running
        return random_products(store, param_dict), SUCCESS

    products = Product.objects.filter(pk__in=results.get('products'),
                                      rescrape=False)
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

def invalidate_session(request):
    #intentrank/invalidate-session
    url = '{0}/intentrank/invalidate-session'.format(INTENTRANK_BASE_URL)
    send_intentrank_request(request, url)
    return HttpResponse("[]", mimetype='application/json')
