import re

from django.contrib.auth.decorators import login_required
from django.db.models import F as Fucking
from django.http import HttpResponse
from django.http.response import Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.assets.models import Category, Page, Store, Tile
from apps.intentrank.controllers import IntentRank
from apps.intentrank.algorithms import ir_all
from apps.intentrank.utils import ajax_jsonp
from apps.utils.models import MemcacheSetting

import scripts.generate_rss_feed as rss_feed


TRACK_SHOWN_TILES_NUM = 20  # move to settings when appropriate


def track_tile_view(request, tile_id):
    """This is a function that accepts a request, not a View.

    Records this tile_id as having been shown for this session.
    If tracking fails, fails silently.
    """
    if not hasattr(request, 'session'):
        print "Warning: session is unavailable; tile views are not being tracked"
        return

    if not isinstance(tile_id, int):
        tile_id = int(tile_id)

    shown = set(request.session.get('shown', []))
    shown.add(tile_id)

    # sets are not JSON serializable, convert to list
    request.session['shown'] = list(shown)


def track_tiles_view(request, tile_ids, reset=False):
    """Shorthand"""
    if reset:
        print "IR tracked tiles reset"
        request.session['shown'] = []
    else:
        limit_showns(request)  # limit is controlled by TRACK_SHOWN_TILES_NUM

    for tile_id in tile_ids:
        track_tile_view(request=request, tile_id=tile_id)

    return request.session.get('shown', [])


def limit_showns(request, n=TRACK_SHOWN_TILES_NUM):
    """
    :param n: how many to keep
    """
    # ordered algos keep track of full list for zero repeats
    # for some algo families, reloading the page should reset the list of shown tiles
    algorithm_name = request.GET.get('algorithm', 'magic').lower()
    
    if algorithm_name in ['magic']:
        # keep a running list of tiles
        pass
    else:
        # default: remember last 20
        request.session['shown'] = request.session.get('shown', [])[-n:]


@never_cache
@csrf_exempt
@require_GET
def get_results_view(request, page_id):
    """Returns random results for a campaign

    :var callback: if given, jsonp callback
    :var url: if given, proxy directly to intentrank.
    :var page: page id
    :var results: int number of results

    :returns HttpResponse/Http404
    """
    algorithm_name = request.GET.get('algorithm', '').lower()
    callback = request.GET.get('callback', None)
    category = request.GET.get('category', None)
    offset = int(request.GET.get('offset', 0))  # used only by some deterministic algos
    num_results = int(request.GET.get('results', 10))
    shown = filter(bool, re.split('(?:,|%2C)', request.GET.get('shown', "")))
    tile_id = request.GET.get('tile-id', 0)  # for related
    session_reset = True if request.GET.get('session-reset', "").lower() == "true" else False
    content_only = (request.GET.get('tile-set', '') == 'content')
    products_only = (request.GET.get('tile-set', '') == 'products')

    # keep track of the last (unique) tiles have been shown, then
    # show everything except these tile ids
    shown_ids = track_tiles_view(request, tile_ids=shown, reset=session_reset)
    offset -= len(shown_ids) # correct for tiles we are removing from queryset

    page = get_object_or_404(Page, id=page_id)

    ir = IntentRank(page=page)
    ir.algorithm = algorithm_name
    algorithm = ir.algorithm

    print 'request for [page {}, feed {}] being handled by {}'.format(
        page.id, page.feed.id, algorithm.__name__)

    # results is a queryset!
    try:
        results = ir.get_results(
            results=num_results,
            request=request, exclude_set=shown_ids, category_name=category,
            offset=offset, tile_id=tile_id, content_only=content_only,
            products_only=products_only)
    except Category.DoesNotExist as e:
        return HttpResponseNotFound("{}".format(e))
    
    # results is a list of stringified tiles!
    results = results.values_list('ir_cache', flat=True)

    # makes sure they are all non-falsy tiles
    results = filter(bool, results)
    print 'returning {0} tiles'.format(len(results))

    # manually construct a json array
    response_text = "[{}]".format(",".join(results))
    if callback:
        response_text = "{0}({1});".format(callback, response_text)
    return HttpResponse(response_text, content_type='application/json')


@login_required
def get_overview(request):
    stores = Store.objects.prefetch_related(
        'pages',
        'pages__feed',
        'pages__feed__tiles',
        'pages__feed__tiles__products',
        'pages__feed__tiles__products__default_image',
        'pages__feed__tiles__products__product_images',
        'pages__feed__tiles__content__tagged_products',
        'pages__feed__tiles__content__tagged_products__default_image',
        'pages__feed__tiles__content__tagged_products__product_images',
    )
    return render_to_response('intentrank/overview.html', {'stores': stores})


@never_cache
@csrf_exempt
@require_GET
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
            tile = get_object_or_404(Tile, id=tile_id)
        except Http404:
            return HttpResponseNotFound("No tile {0}".format(tile_id))

        return ajax_jsonp(tile.to_json())

    # get all tiles
    try:
        page = get_object_or_404(Page, id=page_id)
    except Http404:
        return HttpResponseNotFound("No page {0}".format(page_id))

    feed = page.feed
    if not (feed or tile_id):
        return HttpResponseNotFound("No feed for page {0}".format(page_id))

    # results is a queryset!
    ir = IntentRank(page=page)
    try:
        results = ir.get_results(request=request, algorithm=ir_all)
    except Category.DoesNotExist as e:
        return HttpResponseNotFound("{}".format(e))

    # results is a list of stringified tiles!
    results = results.values_list('ir_cache', flat=True)

    # manually construct a json array
    response_text = "[{}]".format(",".join(results))
    if callback:
        response_text = "{0}({1});".format(callback, response_text)
    return HttpResponse(response_text, content_type='application/json')


@never_cache
@csrf_exempt
@require_GET
def get_rss_feed(request, feed_name, page_id=0, page_slug=None, google=False, **kwargs):
    feed_link = 'http://' + str(request.META['HTTP_HOST']) + '/'
    if page_slug:
        feed_link += str(page_slug) + '/' + str(feed_name)
        page = Page.objects.get(url_slug=page_slug)
    elif page_id:
        feed_link += str(page_id) + '/' + str(feed_name)
        page = Page.objects.get(id=page_id)
    else:
        raise Http404("Feed not found")
    feed = rss_feed.main(page, feed_name=feed_name, feed_link=feed_link, google=google)
    return HttpResponse(feed, content_type='application/rss+xml')


def update_tiles(tile_ids, action='views'):
    """Increment either tiles' 'views' (default) or 'clicks' count by 1."""
    if not tile_ids:
        return

    tracked_tiles = MemcacheSetting.get('track_tiles', True)
    if not tracked_tiles:
        print "Tile tracking disabled by memory-bound setting"
        return

    MemcacheSetting.set('track_tiles', tracked_tiles)  # extend memcache
    try:
        # kwargs is a {<string>: <Fucking>} dict (needed for dynamic key)
        kwargs = {action: Fucking(action) + 1}
        Tile.objects.filter(id__in=tile_ids).update(**kwargs)
    except BaseException:
        # for whatever reason it failed, pause for a while
        MemcacheSetting.set('track_tiles', False)


@never_cache
@csrf_exempt
@require_POST
def track_tiles(request, action, **kwargs):
    tile_ids = request.GET.get('tile-ids', None) or request.POST.get('tile-ids', None)
    if not tile_ids:
        return HttpResponse(status=204)

    tile_ids = [int(x) for x in tile_ids.split(',')]

    update_tiles(tile_ids, action=action)
    return HttpResponse(status=204)
