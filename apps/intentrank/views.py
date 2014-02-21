from django.http.response import Http404
from django.shortcuts import get_object_or_404
import json
import random

from urllib import urlencode
from random import randrange

from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse
from django.template import Context, loader, TemplateDoesNotExist
import httplib2
from mock import MagicMock
from hammock import Hammock
from apps.api.utils import mimic_response

from apps.assets.models import Product, Store, Page
from apps.intentrank.controllers import IntentRank

from apps.intentrank.utils import ajax_jsonp

from apps.pinpoint.models import IntentRankCampaign

SUCCESS = 200
FAIL400 = 400
SUCCESS_STATUSES = xrange(SUCCESS, 300)
DEFAULT_RESULTS  = 12
MAX_BLOCKS_BEFORE_VIDEO = 50


def update_clickstream(request):
    """
    Tells intentrank what producs have been clicked on.

    @param request: The request.

    @return: A json HttpResonse that is empty or contains an error.  Displays nothing on success.
    """

    callback = request.GET.get('callback', 'fn')

    # Proxy is *mostly* deprecated; always succeed
    return ajax_jsonp([], callback, status=SUCCESS)


def get_results(request, **kwargs):
    """Returns random results for a campaign

    kwargs['raw'] also toggles between returning a dictionary
    or an entire HttpResponse.
    """
    # dev proxies to test... test proxies to intentrank-test
    from secondfunnel.settings.test import INTENTRANK_BASE_URL as test_ir

    callback = request.GET.get('callback', None)
    results = int(request.GET.get('results', 10))
    url = kwargs.get('url', None)

    if url:  # straight proxy (for now)
        IntentRankClient = Hammock(test_ir)
        r = IntentRankClient('intentrank')(url).GET(params={'results': results})
        return ajax_jsonp(r.json(), callback_name=callback)

    # otherwise, not a proxy
    page_id = kwargs.get('page', 0)
    page = get_object_or_404(Page, pk=page_id)
    feed = page.feed
    if not feed:
        raise Http404("No feed for page {0}".format(page_id))

    ir = IntentRank(feed=feed)
    return ajax_jsonp(ir.get_results('json', results=results),
                      callback_name=callback)
