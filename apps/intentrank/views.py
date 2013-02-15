import json
from urllib import urlencode
import random
import math

from django.http import HttpResponse
from django.template import Context, Template
import httplib2
from mock import Mock, MagicMock
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

def random_products(store, param_dict, id_only=True):
    """Returns a list of random product ids, as would be returned by IR.

    Only used in development; not in production"""
    store_id = Store.objects.get(slug__exact=store)
    num_results = param_dict.get('results', DEFAULT_RESULTS)
    results = Product.objects.filter(store_id__exact=store_id).order_by('?')

    if id_only:
        results = results.values('id')
        results = map(lambda x: x.get('id'), results)

    if len(results) < num_results:
        results = list(results)
        new_params = {'results': (int(num_results) - len(results))}
        results.extend(list(random_products(store, new_params, id_only)))
        return results
    else:
        return results[:num_results]

def send_intentrank_request(request, url, method='GET', headers=None,
                            http=httplib2.Http):
    if not headers:
        headers = {}

    cookie = request.session.get('ir-cookie')
    if cookie:
        headers['Cookie'] = cookie

    h = http()
    response, content = h.request(
        url,
        method=method,
        headers=headers,
    )

    if response.get('set-cookie'):
        request.session['ir-cookie'] = response['set-cookie']

    return response, content

# TODO: Is there a Guice for Python to inject dependency in live, dev?
def process_intentrank_request(request, store, page, function_name,
                               param_dict):
    """does NOT initiate a real IntentRank request if debug is set to True."""

    url = '{0}/intentrank/store/{1}/page/{2}/{3}'.format(
        INTENTRANK_BASE_URL, store, page, function_name)
    params   = urlencode(param_dict)
    url = '{0}?{1}'.format(url, params)

    if settings.DEBUG:
        # Use a mock instead of avoiding the call
        # Mock is onlt used in development, not in production
        product_results = random_products(store, param_dict, id_only=True)
        json_results = json.dumps({'products': product_results})

        http_mock = Mock()
        http_response = MagicMock(status=SUCCESS)
        http_response.__getitem__.return_value = None
        http_content = json_results
        http_mock.request.return_value = (http_response, http_content)

        http = Mock(return_value=http_mock)
    else:
        http = httplib2.Http

    try:
        response, content = send_intentrank_request(request, url, http=http)
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


def get_json_data(request, products, campaign_id):
    """returns json equivalent of get_blocks' blocks.

    results will be an object {}, not an array [].
    """
    campaign = Campaign.objects.get(pk=campaign_id)
    results = {'products': [],
               'videos': []}

    # products
    for product in products:
        product_props = product.data(raw=True)
        product_js_obj = {}
        for prop in product_props:
            # where product_prop is ('data-key', 'value')
            product_js_obj[prop] = product_props[prop]
        results['products'].append(product_js_obj)

    # videos
    video_cookie = request.session.get('pinpoint-video-cookie')
    if not video_cookie:
        video_cookie = request.session['pinpoint-video-cookie'] = VideoCookie()

    videos = campaign.store.videos.exclude(video_id__in=video_cookie.videos_already_shown)

    # if this is the first batch of results, or the random amount is under the
    # curve of the probability function, then add a video
    show_video = random.random() <= video_probability_function(video_cookie.blocks_since_last, MAX_BLOCKS_BEFORE_VIDEO)
    if videos.exists() and (video_cookie.is_empty() or show_video):
        video = videos.order_by('?')[0]
        results['videos'].append({
            'video_id': video.video_id,
            'video_provider': 'youtube',
            'video_width': '200',
            'video_height': '200',
            'video_autoplay': False
        })
        video_cookie.add_video(video.video_id)
    else:
        video_cookie.add_blocks(len(results))

    request.session['pinpoint-video-cookie'] = video_cookie

    return results


def get_seeds(request, **kwargs):
    """kwargs overrides request values when provided.

    kwargs['raw'] also toggles between returning a dictionary
    or an entire HttpResponse.
    """
    store   = kwargs.get('store', request.GET.get('store', '-1'))
    page    = kwargs.get('campaign', request.GET.get('campaign', '-1'))
    seeds   = kwargs.get('seeds', request.GET.get('seeds', '-1'))
    num_results = kwargs.get('results', request.GET.get('results',
                                                        DEFAULT_RESULTS))

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

    if kwargs.get('raw', False):
        return result
    else:
        return HttpResponse(json.dumps(result), mimetype='application/json',
                            status=status)

def get_results(request, **kwargs):
    """kwargs overrides request values when provided.

    kwargs['raw'] also toggles between returning a dictionary
    or an entire HttpResponse.
    """
    store = kwargs.get('store', request.GET.get('store', '-1'))
    page = kwargs.get('campaign', request.GET.get('campaign', '-1'))
    num_results = kwargs.get('results', request.GET.get('results',
                                                        DEFAULT_RESULTS))

    results, status = process_intentrank_request(
        request, store, page, 'getresults', {
            'results': num_results
        }
    )

    if status in SUCCESS_STATUSES:
        result = get_json_data(request, results, page)

    # workaround for a weird bug on intentrank's side
    elif status == 400:
        return get_seeds(request)

    else:
        result = results

    if kwargs.get('raw', False):
        return result
    else:
        return HttpResponse(json.dumps(result), mimetype='application/json',
                            status=status)


def update_clickstream(request):
    """displays nothing on success."""
    store   = request.GET.get('store', '-1')
    page    = request.GET.get('campaign', '-1')
    product_id = request.GET.get('product_id')

    results, status = process_intentrank_request(request, store, page, 'updateclickstream', {
        'productid': product_id
    })

    if status in SUCCESS_STATUSES:
        # We don't care what we get back
        result = []
    else:
        result = results

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)

def invalidate_session(request):
    #intentrank/invalidate-session
    url = '{0}/intentrank/invalidate-session'.format(INTENTRANK_BASE_URL)
    send_intentrank_request(request, url)
    return HttpResponse("[]", mimetype='application/json')
