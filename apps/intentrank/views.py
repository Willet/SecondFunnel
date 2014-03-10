from threading import Thread, current_thread

from django.conf import settings
from django.http import HttpResponse
from django.http.response import Http404, HttpResponseNotFound
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import request_methods
from apps.assets.models import Page, Tile, TileRelation
from apps.intentrank.controllers import IntentRank
from apps.intentrank.algorithms import ir_generic, ir_all, ir_popular
from apps.intentrank.utils import ajax_jsonp


import scripts.generate_rss_feed as rss_feed


TRACK_SHOWN_TILES_NUM = 20  # move to settings when appropriate


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
    this_thread = current_thread()
    print "{0} started".format(this_thread.name)

    callback = request.GET.get('callback', None)
    results = int(request.GET.get('results', 10))

    # "show everything except these tile ids"
    shown = filter(bool, request.GET.get('shown', "").split(","))
    exclude_set = map(int, shown)

    # keep track of the last (unique) tiles have been shown.
    # limit is controlled by TRACK_SHOWN_TILES_NUM
    if request.session:
        if not request.session.get('shown', []):
            request.session['shown'] = exclude_set
        else:
            request.session['shown'] += exclude_set
        request.session['shown'] = list(set(request.session['shown']))  # uniq
        request.session['shown'] = request.session['shown'][:TRACK_SHOWN_TILES_NUM]

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

    #if related is specified, return all related tile to the given tile-id
    related = request.GET.get('related', None)
    if related is not None and related != '' and related != 'None':
        ir = IntentRank(feed=feed)
        resp = ajax_jsonp(ir.transform(TileRelation.get_related_tiles([Tile.objects.get(old_id=related)])[:100]))
        print "{0} ended".format(this_thread.name)
        return resp

    if request.GET.get('algorithm', None) == 'popular':
        algorithm = ir_popular
    else:
        algorithm = ir_generic

    resp = ajax_jsonp(get_results(feed=feed, results=results,
                                  algorithm=algorithm, request=request,
                                  exclude_set=exclude_set),
                      callback_name=callback)

    print "{0} ended".format(this_thread.name)
    return resp


@never_cache
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

        # Update clicks
        clicks = request.session.get('clicks', [])
        if tile_id not in clicks:
            tile.click()
            for click in clicks:
                TileRelation.relate(Tile.objects.get(old_id=click), tile)
            clicks.append(tile_id)
            request.session['clicks'] = clicks

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

    return ajax_jsonp(get_results(feed=feed, request=request, algorithm=ir_all),
                      callback_name=callback)


def get_results(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                algorithm=ir_generic, **kwargs):
    """Converts a feed into a list of <any> using given parameters.

    :param feed        a <Feed>
    :param results     number of <any> to return
    :param exclude_set IDs of items in the feed to never consider
    :param request     (relay)
    :param algorithm   reference to a <Feed> => [<Tile>] function

    :returns           a list of <any>
    """
    ir = IntentRank(feed=feed)

    # "everything except these tile ids"
    exclude_set = kwargs.get('exclude_set', [])
    request = kwargs.get('request', None)
    return ir.transform(algorithm(feed=feed, results=results,
                                     exclude_set=exclude_set, request=request))


@never_cache
@csrf_exempt
@request_methods('GET')
def get_rss_feed(request, feed_name, page_id=0, page_slug=None, **kwargs):
    feed_link = 'http://' + str(request.META['HTTP_HOST']) + '/'
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
