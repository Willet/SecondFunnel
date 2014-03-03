import json
import time

from django.conf import settings
from django.http import HttpResponse
from django.http.response import Http404, HttpResponseNotFound
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import request_methods
from apps.assets.models import Page, Tile
from apps.intentrank.controllers import IntentRank
from apps.intentrank.algorithms import ir_random, ir_all
from apps.intentrank.utils import ajax_jsonp

import scripts.generate_rss_feed as rss_feed

@never_cache
@csrf_exempt
@request_methods('GET')
def get_results_view(request, page_id):
    """Returns random results for a campaign

    :var url: if given, proxy directly to intentrank.
    :var page: page id
    :var results: int number of results

    :returns HttpResponse/Http404
    """
    callback = request.GET.get('callback', None)
    results = int(request.GET.get('results', 10))

    # "show everything except these tile ids"
    shown = filter(bool, request.GET.get('shown', "").split(","))
    exclude_set = map(int, shown)

    if request.session:
        # keep track of which (unique) tiles have been shown
        request.session['shown'] = list(set(request.session.get('shown', []) +
                                            exclude_set))

    # otherwise, not a proxy
    try:
        page = (Page.objects
                    .filter(old_id=page_id)
                    .select_related('feed__tiles',
                                    'feed__tiles__products',
                                    'feed__tiles__content')
                    .prefetch_related()
                    .get())
    except Page.DoesNotExist:
        return HttpResponseNotFound("No page {0}".format(page_id))

    feed = page.feed
    if not feed:
        return HttpResponseNotFound("No feed for page {0}".format(page_id))
    return ajax_jsonp(get_results(feed=feed, results=results, request=request,
                                  exclude_set=exclude_set),
                      callback_name=callback)


@csrf_exempt
@request_methods('GET')
def get_tiles_view(request, page_id, tile_id=None, **kwargs):
    """Returns a response containing all tiles for the page, or just
    one tile if its id is given.

    (Undocumented, used endpoint)
    It is assumed that the tile format is the same as the ones
    from get_results.
    """
    callback = request.GET.get('callback', None)

    # get single tile
    if tile_id:
        try:
            tile = (Tile.objects
                        .filter(old_id=tile_id)
                        .select_related()
                        .prefetch_related('content', 'products')
                        .get())
        except Tile.DoesNotExist:
            return HttpResponseNotFound("No tile {0}".format(tile_id))

        return ajax_jsonp(tile.to_json())

    # get all tiles
    try:
        page = (Page.objects
                    .filter(old_id=page_id)
                    .select_related('feed__tiles__products',
                                    'feed__tiles__content')
                    .prefetch_related()
                    .get())
    except Page.DoesNotExist:
        return HttpResponseNotFound("No page {0}".format(page_id))

    feed = page.feed
    if not (feed or tile_id):
        return HttpResponseNotFound("No feed for page {0}".format(page_id))

    return ajax_jsonp(get_results(feed=feed, algorithm=ir_all),
                      callback_name=callback, request=request)


def get_results(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS, **kwargs):
    """Supply either feed or page for backward compatibility."""
    ir = IntentRank(feed=feed)

    # "everything except these tile ids"
    exclude_set = kwargs.get('exclude_set', [])
    request = kwargs.get('request', None)
    return ir.transform(ir.ir_random(feed=feed, results=results,
                                     exclude_set=exclude_set, request=request))


@never_cache
@csrf_exempt
@request_methods('GET')
def get_rss_feed(request, feed_name, page_id=0, page_slug=None, **kwargs):
    feed_link = 'http://' + str(request.META['HTTP_HOST']) + '/intentrank/page/'
    if page_slug:
        feed_link += str(page_slug) + '/' + str(feed_name)
        page = Page.objects.get(url_slug=page_slug)
    elif page_id:
        feed_link += str(page_id) + '/' + str(feed_name)
        page = Page.objects.get(old_id=page_id)
    else:
        raise Http404("Feed not found")
    feed = rss_feed.main(page, feed_name=feed_name, feed_link=feed_link)
    return HttpResponse(feed, content_type='application/rss+xml')
