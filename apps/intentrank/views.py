from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import F as Fucking
from django.http import HttpResponse
from django.http.response import Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import request_methods
from apps.assets.models import Page, Tile, Category, Store
from apps.intentrank.controllers import IntentRank, PredictionIOInstance
from apps.intentrank.algorithms import ir_generic, ir_all, ir_base
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

    try:
        with PredictionIOInstance() as predictor:
            predictor.track_tile_view(request, tile_id)
    except BaseException as err:
        print "PredictionIO failed to record tile view"

    if not request.session.get('shown', []):
        request.session['shown'] = [tile_id]
    else:
        request.session['shown'].append(tile_id)
    request.session['shown'] = list(set(request.session['shown']))  # uniq


def track_tiles_view(request, tile_ids):
    """Shorthand"""
    for tile_id in tile_ids:
        track_tile_view(request=request, tile_id=tile_id)
    limit_showns(request)  # limit is controlled by TRACK_SHOWN_TILES_NUM
    return request.session.get('shown', [])


def limit_showns(request, n=TRACK_SHOWN_TILES_NUM):
    """
    :param n: how many to keep
    """
    # ordered algos keep track of full list for zero repeats
    # for some algo families, reloading the page should reset the list of shown tiles
    req_num = request.GET.get('reqNum', 0)
    algorithm_name = request.GET.get('algorithm', 'generic').lower()

    if algorithm_name in ['sorted', 'custom']:
        # prevent these from ever resetting
        pass
    elif algorithm_name in ['generic', 'ordered', 'content_first', 'mixed'] or \
            'finite' in algorithm_name:
        # reset these every pageload
        if int(req_num) == 0:
            request.session['shown'] = []
    else:
        # default: remember last 20
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
    results = int(request.GET.get('results', 10))
    shown = filter(bool, request.GET.get('shown', "").split(","))
    tile_id = request.GET.get('tile-id', 0)  # for related
    session_reset = True if request.GET.get('session-reset', "").lower() == "true" else False

    if session_reset:
        offset = 0  # For deterministic algorithms, we have to reset the offset
        print "intentrank session was cleared"

    # keep track of the last (unique) tiles have been shown, then
    # show everything except these tile ids
    shown = track_tiles_view(request, tile_ids=shown)
    exclude_set = map(int, shown)

    page = get_object_or_404(Page, id=page_id)
    feed = page.feed
    ir = IntentRank(feed=feed)

    algorithm = ir.get_algorithm(algorithm_name)
    print 'request being handled by {0}'.format(algorithm.__name__)

    resp = ajax_jsonp(get_results(feed=feed, results=results,
                                  algorithm=algorithm, request=request,
                                  exclude_set=exclude_set,
                                  category_name=category,
                                  offset=offset, tile_id=tile_id),
                      callback_name=callback)
    return resp


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
            tile = get_object_or_404(Tile, id=tile_id)
        except Tile.DoesNotExist:
            return HttpResponseNotFound("No tile {0}".format(tile_id))

        return ajax_jsonp(tile.to_json())

    # get all tiles
    try:
        page = get_object_or_404(Page, id=page_id)
    except Page.DoesNotExist:
        return HttpResponseNotFound("No page {0}".format(page_id))

    feed = page.feed
    if not (feed or tile_id):
        return HttpResponseNotFound("No feed for page {0}".format(page_id))

    return ajax_jsonp(get_results(feed=feed, request=request, algorithm=ir_all),
                      callback_name=callback)


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
    if not feed.tiles.count():  # short circuit: return empty resultset
        return IntentRank(True).transform([])

    ir = IntentRank(feed=feed)

    # "everything except these tile ids"
    exclude_set = kwargs.get('exclude_set', [])
    request = kwargs.get('request', None)
    category_name = kwargs.get('category_name', None)
    if category_name:
        category = Category.objects.get(name=category_name)
        products = category.products.all()
        allowed_set = []
        for product in products:
            allowed_set += [t.id for t in product.tiles.all()]
            contents = product.content.all()
            for content in contents:
                allowed_set += [tile.id for tile in content.tiles.all()]
        allowed_set = list(set(allowed_set))
    else:
        allowed_set = None

    tiles = ir_base(feed=feed, allowed_set=allowed_set)
    return ir.render(algorithm, tiles=tiles, results=results,
                     exclude_set=exclude_set, allowed_set=allowed_set,
                     request=request, offset=offset, tile_id=tile_id, feed=feed)


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


def update_tiles(tile_ids, action='views'):
    """Increment either tiles' 'views' (default) or 'clicks' count by 1."""
    if not tile_ids:
        return

    track_tiles = MemcacheSetting.get('track_tiles', True)
    if not track_tiles:
        print "Tile tracking disabled by memory-bound setting"
        return

    MemcacheSetting.set('track_tiles', track_tiles)  # extend memcache
    try:
        # kwargs is a {<string>: <Fucking>} dict (needed for dynamic key)
        kwargs = {action: Fucking(action) + 1}
        Tile.objects.filter(id__in=tile_ids).update(**kwargs)
    except BaseException as err:
        # for whatever reason it failed, pause for a while
        MemcacheSetting.set('track_tiles', False)


@never_cache
@csrf_exempt
@request_methods('POST')
def track_tiles(request, action, **kwargs):
    tile_ids = request.GET.get('tile-ids', None) or request.POST.get('tile-ids', '')
    tile_ids = map(int, tile_ids.split(','))

    update_tiles(tile_ids, action=action)
    return HttpResponse(status=204)
