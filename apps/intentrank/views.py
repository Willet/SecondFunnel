from django.http.response import Http404
from django.shortcuts import get_object_or_404

from hammock import Hammock

from apps.assets.models import Page
from apps.intentrank.controllers import IntentRank

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

    url = kwargs.get('url', None)
    if url:  # temporary proxy
        return ajax_jsonp(get_results_ir(url=url, results=results),
                          callback_name=callback)

    # otherwise, not a proxy
    page_id = kwargs.get('page', 0)
    page = get_object_or_404(Page, pk=page_id)
    feed = page.feed
    if not feed:
        raise Http404("No feed for page {0}".format(page_id))
    return ajax_jsonp(get_results(feed=feed, results=results),
                      callback_name=callback)


def get_results_ir(url, results):
    # dev proxies to test... test proxies to intentrank-test
    from secondfunnel.settings.test import INTENTRANK_BASE_URL as test_ir

    IntentRankClient = Hammock(test_ir)
    r = IntentRankClient('intentrank')(url).GET(params={'results': results})
    return r.json()


def get_results(results, **kwargs):
    """Supply either feed or page for backward compatibility."""
    feed = kwargs.get('feed')
    if not feed and kwargs.get('page'):
        feed = kwargs['page'].feed

    # arbitrary arguments accepted by intentrank
    kw = {'results': results}

    request = kwargs.get('request')
    if request:
        kw['request'] = request

    ir = IntentRank(feed=feed)
    return ir.get_results('json', **kw)
