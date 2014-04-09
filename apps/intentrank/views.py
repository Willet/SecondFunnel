from django.conf import settings
from django.db.transaction import atomic
from django.http import HttpResponse
from django.http.response import Http404, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import request_methods
from apps.assets.models import Page, Tile, TileRelation, Category
from apps.intentrank.controllers import IntentRank
from apps.intentrank.algorithms import ir_generic, ir_all
from apps.intentrank.utils import ajax_jsonp
from apps.utils import thread_id
from apps.utils.models import MemcacheSetting

import scripts.generate_rss_feed as rss_feed


TRACK_SHOWN_TILES_NUM = 20  # move to settings when appropriate


def track_tile_view(request, tile_id):
    """This is a function that accepts a request, not a View.

    Records this tile_id as having been shown for this session.
    If tracking fails, fails silently.
    """
    if not hasattr(request, 'session'):
        return

    tile_id = int(tile_id)

    if not request.session.get('shown', []):
        request.session['shown'] = [tile_id]
    else:
        request.session['shown'].append(tile_id)
    request.session['shown'] = list(set(request.session['shown']))  # uniq


def track_tiles_view(request, tile_ids):
    """Shorthand"""
    for tile_id in tile_ids:
        track_tile_view(request=request, tile_id=tile_id)


def limit_showns(request, n=TRACK_SHOWN_TILES_NUM):
    """
    :param n: how many to keep
    """
    # ordered algos keep track of full list for zero repeats
    if not request.GET.get('algorithm', None) in [
        'ordered', 'sorted', 'finite', 'custom']:
        request.session['shown'] = request.session.get('shown', [])[-n:]


@never_cache
@csrf_exempt
@thread_id
@request_methods('GET')
def get_results_view(request, page_id):
    """Returns random results for a campaign

    :var callback: if given, jsonp callback
    :var url: if given, proxy directly to intentrank.
    :var page: page id
    :var results: int number of results

    :returns HttpResponse/Http404
    """
    algorithm_name = request.GET.get('algorithm', 'generic').lower()
    callback = request.GET.get('callback', None)
    category = request.GET.get('category', None)
    offset = int(request.GET.get('offset', 0))  # used only by some deterministic algos
    related = request.GET.get('related', '')
    results = int(request.GET.get('results', 10))
    shown = filter(bool, request.GET.get('shown', "").split(","))
    tile_id = request.GET.get('tile-id', 0)  # for related

    #if related is specified, return all related tile to the given tile-id
    if related:
        algorithm_name = 'related'
        tile_id = related

    # keep track of the last (unique) tiles have been shown.
    track_tiles_view(request, tile_ids=shown)

    # "show everything except these tile ids"
    exclude_set = map(int, request.session.get('shown', []))

    limit_showns(request)  # limit is controlled by TRACK_SHOWN_TILES_NUM

    page = get_object_or_404(Page, id=page_id)
    feed = page.feed
    ir = IntentRank(feed=feed)

    # find the appropriate algorithm.
    if algorithm_name == 'finite_popular':
        # the client calls it something else.
        algorithm = getattr(ir, 'ir_finite_by')('-weighted_clicks_per_view')
    elif 'finite_by_' in algorithm_name:
        algorithm = ir.ir_finite_by(algorithm_name[10:])
    else:
        algorithm = getattr(ir, 'ir_' + algorithm_name) or ir.ir_generic

    resp = ajax_jsonp(get_results(feed=feed, results=results,
                                  algorithm=algorithm, request=request,
                                  exclude_set=exclude_set, category=category,
                                  offset=offset, tile_id=tile_id),
                      callback_name=callback)
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
                        .filter(id=tile_id)
                        .select_related()
                        .prefetch_related('content', 'products')
                        .get())
        except Tile.DoesNotExist:
            return HttpResponseNotFound("No tile {0}".format(tile_id))

        # Update clicks
        clicks = request.session.get('clicks', [])
        expired_tiles = []
        if tile_id not in clicks:
            for click in clicks:
                try:
                    TileRelation.relate(Tile.objects.get(id=click), tile)
                except Tile.DoesNotExist as err:
                    # session kept track of a tile that isn't in the db;
                    # remove tile from session
                    expired_tiles.append(click)

            clicks.append(tile_id)
            clicks = [x for x in clicks if not x in expired_tiles]
            request.session['clicks'] = clicks

        return ajax_jsonp(tile.to_json())

    # get all tiles
    try:
        page = (Page.objects
                    .filter(id=page_id)
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


@never_cache
@csrf_exempt
@request_methods('GET')
def get_related_tiles_view(request, page_id, tile_id=None, **kwargs):
    """Returns a response containing a list of tiles related to the given
    tile in order of popularity.

    The tile format is the same as the ones from get_tiles_view.
    """
    callback = request.GET.get('callback', None)

    # get tile
    try:
        tile = Tile.objects.get(id=tile_id)
    except Tile.DoesNotExist:
        return HttpResponseNotFound("No tile {0}".format(tile_id))

    return ajax_jsonp(tile.get_related(), callback_name=callback)


def get_results(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS,
                algorithm=ir_generic, tile_id=0, offset=0, **kwargs):
    """Converts a feed into a list of <any> using given parameters.

    :param feed        a <Feed>
    :param results     number of <any> to return
    :param exclude_set IDs of items in the feed to never consider
    :param request     (relay)
    :param algorithm   reference to a <Feed> => [<Tile>] function
    :param tile_id     for getting related tiles

    :returns           a list of <any>
    """
    ir = IntentRank(feed=feed)

    # "everything except these tile ids"
    exclude_set = kwargs.get('exclude_set', [])
    request = kwargs.get('request', None)
    category_name = kwargs.get('category', None)
    if category_name:
        category = Category.objects.get(name=category_name)
        allowed_set = [getattr(tile, 'id', getattr(tile, 'old_id'))
                       for tile in list(Tile.objects.filter(tile__products__in=category.products))]
    else:
        allowed_set = None
    return ir.render(algorithm, feed=feed, results=results,
                     exclude_set=exclude_set, allowed_set=allowed_set,
                     request=request, offset=offset, tile_id=tile_id)


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
        page = Page.objects.get(id=page_id)
    else:
        raise Http404("Feed not found")
    feed = rss_feed.main(page, feed_name=feed_name, feed_link=feed_link)
    return HttpResponse(feed, content_type='application/rss+xml')


@atomic
def update_tiles(request, tile_function, **kwargs):
    """This is a view helper that happens to accept 'request'."""
    tile_id = kwargs.get('tile_id', None) or request.GET.get('tile-id', None)
    tile_ids = request.GET.get('tile-ids', None) or request.POST.get('tile-ids', '')
    if tile_id:
        tile = get_object_or_404(Tile, id=tile_id)
        tile_function(tile)
    elif tile_ids:
        tile_ids = tile_ids.split(',')
        tiles = get_list_or_404(Tile, id__in=tile_ids)
        for tile in tiles:
            tile_function(tile)
    else:
        return HttpResponseBadRequest()
    return HttpResponse('', status=204)


@never_cache
@csrf_exempt
@request_methods('POST')
def click_tile(request, **kwargs):
    """Register a click, doing whatever tracking it needs to do."""

    track_tiles = MemcacheSetting.get('track_tiles', True)
    MemcacheSetting.set('track_tiles', track_tiles)  # extend memcache

    def click_func(tile):
        clicks = request.session.get('clicks', [])
        if tile.id not in clicks:
            for click in clicks:
                TileRelation.relate(Tile.objects.get(id=click), tile)
            clicks.append(tile.id)
            request.session['clicks'] = clicks
        tile.add_click()

    if not track_tiles:
        print "Tile tracking disabled by memory-bound setting"
        return HttpResponse(status=204)

    try:
        return update_tiles(request, tile_function=click_func, **kwargs)
    except:
        # for whatever reason it failed, pause for a while
        MemcacheSetting.set('track_tiles', False)
    return HttpResponse(status=204)  # pretend it succeeded


@never_cache
@csrf_exempt
@request_methods('POST')
def view_tile(request, **kwargs):

    track_tiles = MemcacheSetting.get('track_tiles', True)
    MemcacheSetting.set('track_tiles', track_tiles)  # extend memcache

    def view_func(tile):
        tile.add_view()
        track_tile_view(request=request, tile_id=tile.id)

    if not track_tiles:
        print "Tile tracking disabled by memory-bound setting"
        return HttpResponse(status=204)

    try:
        return update_tiles(request, tile_function=view_func, **kwargs)
    except:
        # for whatever reason it failed, pause for a while
        MemcacheSetting.set('track_tiles', False)
    return HttpResponse(status=204)  # pretend it succeeded
