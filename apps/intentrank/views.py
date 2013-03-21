import httplib2
import json
import math
import random

from urllib import urlencode
from random import randrange, choice

from django.conf import settings
from django.http import HttpResponse
from django.db.models import Count
from mock import MagicMock
from apps.assets.models import Product, Store

# All requests are get requests at the moment
# URL to IntentRank looks something like this:
# /intentrank/intentrank/store/<STORE SLUG>/page/<PAGE ID>/<FUNCTION>

# getseeds?seeds=1,2,3,4&results=2
from apps.pinpoint.models import Campaign
from secondfunnel.settings.common import INTENTRANK_BASE_URL

SUCCESS = 200
REDIRECT = 300
FAIL400 = 400
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
    num_results = int(param_dict.get('results', DEFAULT_RESULTS))
    results = []

    while len(results) < num_results:
        query_set = Product.objects.select_related()\
                           .prefetch_related('lifestyleImages')\
                           .annotate(num_images=Count('media'))\
                           .filter(store_id__exact=store_id,
                                   num_images__gt=0)[:num_results]
        results_partial = list(query_set)

        if id_only:
            results_partial = map(lambda x: x.id, results_partial)

        results.extend(results_partial)

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
    """does NOT initiate a real IntentRank request if debug is set to True.

    Returns the exact number of products requested only when debug is True.
    """

    url = '{0}/intentrank/store/{1}/page/{2}/{3}'.format(
        INTENTRANK_BASE_URL, store, page, function_name)
    params   = urlencode(param_dict)
    url = '{0}?{1}'.format(url, params)

    if settings.DEBUG:
        # Use a mock instead of avoiding the call
        # Mock is onlt used in development, not in production
        results = {'products': random_products(store, param_dict, id_only=True)}

        response = MagicMock(status=SUCCESS)
    else:  # live
        http = httplib2.Http

        try:
            response, content = send_intentrank_request(request, url, http=http)
        except httplib2.HttpLib2Error:
            # something fundamentally went wrong, and we have nothing to show
            response = MagicMock(status=FAIL400)
            content = "{}"

        try:
            results = json.loads(content)
        except ValueError:
            results = {"error": content}

    if 'error' in results:
        results.update({'url': url})
        return results, response.status

    products = Product.objects.annotate(num_images=Count('media'))\
                              .filter(pk__in=results.get('products'),
                                      num_images__gt=0,
                                      rescrape=False)

    return products, response.status


def get_json_data(request, products, campaign_id, seeds=None):
    """returns json equivalent of get_blocks' blocks.

    seeds is a list of product IDs.

    results will be an object {}, not an array [].
    products_with_images_only should be either '0' or '1', please.
    """
    campaign = Campaign.objects.get(pk=campaign_id)
    results = []
    products_with_images_only = True
    if request.GET.get('products_with_images_only', '1') == '0':
        products_with_images_only = False

    # products
    for product in products:
        if not product.images() and products_with_images_only:
            continue  # has no image, but wanted image --> ignore product

        product_props = product.data(raw=True)
        product_js_obj = {}
        for prop in product_props:
            # where product_prop is ('data-key', 'value')
            product_js_obj[prop] = product_props[prop]
        results.append(product_js_obj)

    # videos
    video_cookie = request.session.get('pinpoint-video-cookie')
    if not video_cookie:
        video_cookie = request.session['pinpoint-video-cookie'] = VideoCookie()

    videos = campaign.store.videos.exclude(video_id__in=video_cookie.videos_already_shown)

    # if this is the first batch of results, or the random amount is under the
    # curve of the probability function, then add a video
    show_video = random.random() <= video_probability_function(
        video_cookie.blocks_since_last, MAX_BLOCKS_BEFORE_VIDEO)
    if videos.exists() and (video_cookie.is_empty() or show_video):
        video = videos.order_by('?')[0]
        results.append({
            'id': video.video_id,
            'url': 'http://www.youtube.com/watch?v={0}'.format(video.video_id),
            'provider': 'youtube',
            'width': '450',
            'height': '250',
            'autoplay': 0,
            'template': 'youtube'
        })
        video_cookie.add_video(video.video_id)
    else:
        video_cookie.add_blocks(len(results))

    request.session['pinpoint-video-cookie'] = video_cookie

    # store-wide external content
    external_content = campaign.store.external_content.filter(
        active=True, approved=True)

    # content to product ration. e.g., 2 == content to products 2:1
    content_to_products = 1

    need_to_show = int(round(len(results) * content_to_products))

    if len(external_content) > 0 and need_to_show > 0:
        need_to_show = min(need_to_show, len(external_content))

        for item in random.sample(external_content, need_to_show):
            json_content = item.to_json()
            json_content.update({
                'template': item.content_type.name.lower()
            })

            related_products = item.tagged_products.all()
            if related_products:
                related_json = [x.data(raw=True) for x in related_products]

                json_content.update({
                    'related-products': related_json
                })


            results.insert(randrange(len(results) + 1), json_content)

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
        result = get_json_data(request, results, page,
                               seeds=filter(None, str(seeds).split(',')))
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
    seeds   = kwargs.get('seeds', request.GET.get('seeds', '-1'))
    num_results = kwargs.get('results', request.GET.get('results',
                                                        DEFAULT_RESULTS))

    results, status = process_intentrank_request(
        request, store, page, 'getresults', {
            'results': num_results
        }
    )

    if status in SUCCESS_STATUSES:
        result = get_json_data(request, results, page,
                               seeds=filter(None, seeds.split(',')))

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
