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
DEFAULT_RESULTS = 12
MAX_BLOCKS_BEFORE_VIDEO = 50


class VideoCookie(object):
    """
    Defines a cookie that tracks how many blocks have been placed since
    the last video has been placed, and what videos have already been placed.

    @ivar blocks_since_last: The number of blocks since the last video.
    @ivar videos_already_shown: A list of video ids already shown.
    """

    def __init__(self):
        """
        Creates a new video cookie that is empty (has no blocks since last
        video and no videos already shown).
        """
        self.blocks_since_last = 0
        self.videos_already_shown = []

    def add_video(self, video_id):
        """
        Adds a video to the list of videos already shown.

        @param video_id: The id of the video to add.

        @return: self
        """
        self.videos_already_shown.append(video_id)
        self.blocks_since_last = 0
        return self

    def add_blocks(self, blocks):
        """
        Adds blocks to the number of blocks since a video was shown.

        @param blocks: The number of blocks to add.

        @return: self
        """
        self.blocks_since_last += blocks
        return self

    def is_empty(self):
        """
        Checks if the cookie is empty (no blocks since last and
        no videos already shown).

        @return: Whether the cookie is empty.
        """
        return self.blocks_since_last == 0 \
            and self.videos_already_shown == []

    def __str__(self):
        """
        String representation of a VideoCookie

        @return: A string representation of a VideoCookie
        """
        return str(self.blocks_since_last) + ", " + str(self.videos_already_shown)


def video_probability_function(x, m):
    """
    This is a probability function for determining when youtube
    videos are shown.

    Here's this function on wolfram alpha: U{http://wolfr.am/YpGRZe}

    @param x: The current number of blocks added since the last video.
    @param m: The maximum number of blocks before a video is added.

    @return: A number in the range [0, 1] which represents the
    probability of a video showing up.
    """
    if x <= 0:
        return 0
    elif x >= m:
        return 1
    else:
        return 1 - (math.log(m - x) / math.log(m))


def random_products(store, num_results):
    """
    Gets a specified number of random products from a store.

    @param store: The store to get products from.
    @param num_results: The number of results to get.

    @return: The requested number of products.
    """
    store_id = Store.objects.get(slug__exact=store)
    results = Product.objects.filter(store_id__exact=store_id).order_by('?')
    if len(results) < num_results:
        results = list(results)
        results.extend(list(random_products(store, (num_results) - len(results))))
        return results
    else:
        return results[:num_results]


def send_intentrank_request(request, url, method='GET', headers=None):
    """
    Sends a given request to intentrank with the given headers.

    @param request: The request to the django intentrank api.
    @param url: The url to the intentrank service.
    @param method:
    @param headers: The headers for the request to the intentrank service.

    @return: A tuple with a response code and the content that was returned.
    """
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
    """
    Processes an intentrank request, builing the correct url and sending the request.

    @param request: The request to the django intentrank api.
    @param store: The store this request is for.
    @param page: The page this request is for.
    @param function_name: The intentrank api function to call.
    @param param_dict: The query parameters to send to intentrank.

    @return: A tuple with QuerySet of products and a response status.
    """
    url = '{0}/intentrank/store/{1}/page/{2}/{3}'.format(
        INTENTRANK_BASE_URL, store, page, function_name)
    params = urlencode(param_dict)
    url = '{0}?{1}'.format(url, params)

    if settings.DEBUG:
        return random_products(
            store, int(param_dict.get('results', DEFAULT_RESULTS))), SUCCESS

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
    """
    Renders the given products and appends them to the given results list.

    @param products: The products to add to the results.
    @param campaign: The page that this request is being processed for.
    @param results: The list of results to add rendered products to.
    """
    # Get theme
    theme = campaign.store.theme
    discovery_theme = "".join([
        "{% load pinpoint_ui %}",
        "<div class='block product' {{product.data|safe}}>",
        theme.discovery_product,
        "</div>"
    ])

    for product in products:
        context = Context()
        context.update({
            'product': product
        })
        results.append(Template(discovery_theme).render(context))


def videos_to_template(request, campaign, results):
    """
    Determines if a video should be added to the results using video_probability_function.
    If a video is to be added, then this renderes a random video that hasn't been seen
    on the current page, and adds it to the results.

    @param request: The request to the django intentrank api.
    @param campaign: The page that this request is for.
    @param results: The list to add rendered videos to.
    """
    theme = campaign.store.theme
    discovery_youtube_theme = "".join([
        "{% load pinpoint_ui %}",
        "{% load pinpoint_youtube %}",
        "<div class='block youtube wide'>",
        theme.discovery_youtube,
        "</div>"
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
    """
    Generates a list of discovery blocks of different types.

    @param request: The request to the django intentrank api.
    @param products: The QuerySet of products to render.
    @param campaign_id: The page this request is for.

    @return: A list of rendered discovery blocks.
    """
    campaign = Campaign.objects.get(pk=campaign_id)
    results = []
    products_to_template(products, campaign, results)
    videos_to_template(request, campaign, results)
    return results


def get_seeds(request):
    """
    Gets initial seeds for a page. Should be called when a page loads.

    @param request: The request.

    @return: A json HttpResonse that contains rendered products or an error.
    """
    store = request.GET.get('store', '-1')
    page = request.GET.get('campaign', '-1')
    seeds = request.GET.get('seeds', '-1')
    num_results = request.GET.get('results', DEFAULT_RESULTS)

    request.session['pinpoint-video-cookie'] = VideoCookie()

    results, status = process_intentrank_request(
        request, store, page, 'getseeds', {
            'seeds': seeds,
            'results': num_results
        }
    )

    if status in SUCCESS_STATUSES:
        result = get_blocks(request, results, page)
    else:
        result = results

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)


def get_results(request):
    """
    Gets products using intentrank.

    @param request: The request.

    @return: A json HttpResonse that contains rendered products or an error.
    """
    store = request.GET.get('store', '-1')
    page = request.GET.get('campaign', '-1')
    num_results = request.GET.get('results', DEFAULT_RESULTS)

    results, status = process_intentrank_request(
        request, store, page, 'getresults', {
            'results': num_results
        }
    )

    if status in SUCCESS_STATUSES:
        result = get_blocks(request, results, page)
    else:
        result = results

    return HttpResponse(json.dumps(result), mimetype='application/json',
                        status=status)


def update_clickstream(request):
    """
    Tells intentrank what producs have been clicked on.

    @param request: The request.

    @return: A json HttpResonse that is empty or contains an error.
    """
    store = request.GET.get('store', '-1')
    page = request.GET.get('campaign', '-1')
    product_id = request.GET.get('product_id')

    results, status = process_intentrank_request(request, store, page, 'updateclickstream', {
        'product_id': product_id
    })

    # Return JSON results
    return HttpResponse(json.dumps(results), mimetype='application/json', status=status)


def invalidate_session(request):
    """
    Invalidates an intentrank session.

    @param request: The request.

    @return: An empty json HttpResonse.
    """
    #intentrank/invalidate-session
    url = '{0}/intentrank/invalidate-session'.format(INTENTRANK_BASE_URL)
    send_intentrank_request(request, url)
    return HttpResponse("[]", mimetype='application/json')
