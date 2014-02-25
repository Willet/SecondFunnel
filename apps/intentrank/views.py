from django.conf import settings
from django.http.response import Http404, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from hammock import Hammock

from apps.assets.models import Page, Tile
from apps.intentrank.controllers import IntentRank
from apps.intentrank.algorithms import ir_random, ir_all
from apps.intentrank.utils import ajax_jsonp


def get_results_view(request, **kwargs):
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

    url = kwargs.get('url', None)
    if url:  # temporary proxy
        return ajax_jsonp(get_results_ir(url=url, results=results),
                          callback_name=callback)

    # otherwise, not a proxy
    page_id = kwargs.get('page_id', 0)
    try:
        page = Page.objects.filter(old_id=page_id).get()
    except Page.DoesNotExist:
        return HttpResponseNotFound("No page {0}".format(page_id))

    feed = page.feed
    if not feed:
        return HttpResponseNotFound("No feed for page {0}".format(page_id))
    return ajax_jsonp(get_results(feed=feed, results=results,
                                  exclude_set=exclude_set),
                      callback_name=callback)


def get_tiles_view(request, page_id, tile_id=None, **kwargs):
    """Returns a response containing all tiles for the page, or just
    one tile if its id is given.

    (Undocumented, used endpoint)
    It is assumed that the tile format is the same as the ones
    from get_results.
    """
    callback = request.GET.get('callback', None)
    results = int(request.GET.get('results', 10))

    try:
        page = Page.objects.filter(old_id=page_id).get()
    except Page.DoesNotExist:
        return HttpResponseNotFound("No page {0}".format(page_id))

    feed = page.feed
    if not feed:
        raise Http404("No feed for page {0}".format(page_id))
    if tile_id:
        try:
            tile = Tile.objects.filter(old_id=tile_id).get()
        except Tile.DoesNotExist:
            return HttpResponseNotFound("No tile {0}".format(tile_id))

        return ajax_jsonp(tile.to_json())

    return ajax_jsonp(get_results(feed=feed, algorithm=ir_all),
                      callback_name=callback)


def get_results_ir(url, results):
    """Access the Real intentrank. For all other uses, see get_results."""
    # dev proxies to test... test proxies to intentrank-test
    from secondfunnel.settings.test import INTENTRANK_BASE_URL as test_ir

    if settings.ENVIRONMENT == 'test':
        # test should never proxy to itself -- it makes no sense
        test_ir = 'http://intentrank-test.elasticbeanstalk.com'

    IntentRankClient = Hammock(test_ir)
    r = IntentRankClient('intentrank')(url).GET(params={'results': results})
    return r.json()


def get_results(feed, results=settings.INTENTRANK_DEFAULT_NUM_RESULTS, **kwargs):
    """Supply either feed or page for backward compatibility."""
    ir = IntentRank(feed=feed)

    # "everything except these tile ids"
    exclude_set = kwargs.get('exclude_set', [])
    return ir.transform(ir.ir_random(feed=feed, results=results,
                                     exclude_set=exclude_set))
