import json
from urllib import urlencode
import random
import math

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

SUCCESS = 200
REDIRECT = 300
SUCCESS_STATUSES = xrange(SUCCESS, REDIRECT)
DEFAULT_RESULTS  = 12
MAX_BLOCKS_BEFORE_VIDEO = 50

class VideoCookie(object):
    def __init__(self):
        self.blocks_since_last = 0
        self.videos_already_shown = []

    def add_video(self, video_id):
        self.videos_already_shown.append(video_id)
        self.blocks_since_last = 0
        return self

    def add_blocks(self, blocks):
        self.blocks_since_last += blocks
        return self

    def is_empty(self):
        return self.blocks_since_last == 0 \
           and self.videos_already_shown == []

    def __str__(self):
        return str(self.blocks_since_last) + ", " + str(self.videos_already_shown)


def video_probability_function(x, m):
    if x <= 0:
        return 0
    elif x >= m:
        return 1
    else:
        return 1 - (math.log(m - x) / math.log(m))

def random_products(store, param_dict):
    store_id = Store.objects.get(slug__exact=store)
    num_results = param_dict.get('results', DEFAULT_RESULTS)
    results = Product.objects.filter(store_id__exact=store_id).order_by('?')
    if len(results) < num_results:
        results = list(results)
        results.extend(list(random_products(store, {
            'results': (int(num_results) - len(results))
        })))
        return results
    else:
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
    """does NOT initiate a real IntentRank request if debug is set to True."""

    url = '{0}/intentrank/store/{1}/page/{2}/{3}'.format(
        INTENTRANK_BASE_URL, store, page, function_name)
    params   = urlencode(param_dict)
    url = '{0}?{1}'.format(url, params)

    if settings.DEBUG:
        return random_products(store, param_dict), SUCCESS

    try:
        response, content = send_intentrank_request(request, url)
    except httplib2.HttpLib2Error:
        content = "{}"

    try:
        results = json.loads(content)
    except ValueError:
        results = {"error": content}

    if 'error' in results:
        results.update({'url': url})
        return results, response.status

    products = Product.objects.filter(pk__in=results.get('products'),
                                      rescrape=False)
    return products, response.status

# TODO: We shouldn't be doing this on the backend
# Might make more sense to just use JS templates on the front end for
# consistency
def products_to_template(products, campaign, results):
    # Get theme
    theme    = campaign.store.theme
    discovery_theme = "".join([
        "{% load pinpoint_ui %}",
        "<div class='block product' {{product.data|safe}}>",
        theme.discovery_product,
        "</div>",
    ])

    for product in products:
        context = Context()
        context.update({
            'product': product
        })
        results.append(Template(discovery_theme).render(context))


def videos_to_template(request, campaign, results):
    theme = campaign.store.theme
    discovery_youtube_theme = "".join([
        "{% load pinpoint_ui %}",
        "{% load pinpoint_youtube %}",
        "<div class='block youtube wide'>",
        theme.discovery_youtube,
        "</div>",
    ])

    video_cookie = request.session.get('pinpoint-video-cookie')
    if not video_cookie:
        video_cookie = request.session['pinpoint-video-cookie'] = VideoCookie()

    videos = campaign.store.videos.exclude(video_id__in=video_cookie.videos_already_shown)

    # if this is the first batch of results, or the random amount is under the
    # curve of the probability function, then add a video
    show_video = random.random() <= video_probability_function(video_cookie.blocks_since_last, MAX_BLOCKS_BEFORE_VIDEO)
    if videos.exists() and (video_cookie.is_empty() or show_video):
        video = videos.order_by('?')[0]
        context = Context()
        context.update({
            'video': video
        })
        if len(results) == 0:
            position = 0
        else:
            position = random.randrange(len(results))
        results.insert(position, Template(discovery_youtube_theme).render(context))
        video_cookie.add_video(video.video_id)
        video_cookie.add_blocks(len(results) - position)
    else:
        video_cookie.add_blocks(len(results))

    request.session['pinpoint-video-cookie'] = video_cookie


# combines inserting products and youtube videos
def get_blocks(request, products, campaign_id):
    campaign = Campaign.objects.get(pk=campaign_id)
    results = []
    products_to_template(products, campaign, results)
    videos_to_template(request, campaign, results)
    return results


def get_json_data(request, products, campaign_id):
    """returns json equivalent of get_blocks' blocks.

    results will be an object {}, not an array [].
    """
    campaign = Campaign.objects.get(pk=campaign_id)
    results = {'products': [],
               'discoveryProductTemplate': ''}
    for product in products:
        product_props = product.data(raw=True)
        product_js_obj = {}
        for product_prop in product_props:
            # where product_prop is ('data-key', 'value')
            product_js_obj[product_prop[0]] = product_prop[1]
        results['products'].append(product_js_obj)

    # TODO
    # videos_to_template(request, campaign, results)

    # TODO
    theme = campaign.store.theme
    results['discoveryProductTemplate'] = "".join([
        "<!-- load pinpoint_ui -->",
        "<div class='block product' {{ productData }}>",
        theme.discovery_product,
        "</div>",
    ])

    return results


def get_seeds(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    seeds   = request.GET.get('seeds', '-1')
    num_results = request.GET.get('results', DEFAULT_RESULTS)

    request.session['pinpoint-video-cookie'] = VideoCookie()

    results, status = process_intentrank_request(
        request, store, page, 'getseeds', {
        'seeds'  : seeds,
        'results': num_results
        }
    )

    if status in SUCCESS_STATUSES:
        result = get_json_data(request, results, page)
    else:
        result = results

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)

def get_results(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    num_results = request.GET.get('results', DEFAULT_RESULTS)

    results, status = process_intentrank_request(
        request, store, page, 'getresults', {
            'results': num_results
        }
    )

    if status in SUCCESS_STATUSES:
        result = get_json_data(request, results, page)
    else:
        result = results

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)

def update_clickstream(request):
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    product_id = request.GET.get('product_id')

    results, status = process_intentrank_request(request, store, page, 'updateclickstream', {
        'product_id': product_id
    })

    # Return JSON results
    return HttpResponse(json.dumps(results), mimetype='application/json', status=status)

def invalidate_session(request):
    #intentrank/invalidate-session
    url = '{0}/intentrank/invalidate-session'.format(INTENTRANK_BASE_URL)
    send_intentrank_request(request, url)
    return HttpResponse("[]", mimetype='application/json')
