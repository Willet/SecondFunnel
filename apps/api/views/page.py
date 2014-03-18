import json
from socket import error as socket_error, errno
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import check_login, request_methods
from apps.api.paginator import BaseCGHandler
from apps.api.resources import ContentGraphClient
from apps.api.utils import mimic_response
from apps.assets.models import Page, Store, Product
from apps.intentrank.utils import ajax_jsonp, returns_cg_json
from apps.static_pages.views import (generate_static_campaign,
                                     transfer_static_campaign)
from apps.static_pages.tasks import generate_static_campaign as async_generate_campaign


class PageCGHandler(BaseCGHandler):
    model = Page

    def patch(self, request, *args, **kwargs):
        page = get_object_or_404(self.model, old_id=kwargs.get('page_id'))
        page.update(**json.loads(request.body))
        page.save()
        return page.to_cg_json()


class StorePageCGHandler(PageCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, old_id=store_id)
        self.store_id = store.id

        return super(StorePageCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StorePageCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id)


@check_login
@csrf_exempt
@request_methods('POST', 'PUT', 'PATCH')
def generate_static_page(request, store_id, page_id):
    """alias"""
    return generate_static_campaign(request, store_id, page_id=page_id)


@check_login
@csrf_exempt
@request_methods('POST')
def transfer_static_page(request, store_id, page_id):
    try:
        results = transfer_static_campaign(store_id, page_id)
        return ajax_jsonp(results)
    except BaseException as err:
        return ajax_jsonp({
            'success': False,
            'exception': err.__class__.__name__,
            'reason': err.message
        }, status=500)

@check_login
@csrf_exempt
@request_methods('GET', 'PATCH')
def modify_page(request, store_id, page_id):
    if request.method == 'GET':
        r = ContentGraphClient.store(store_id).page(page_id).GET(params=request.GET)
    elif request.method == 'PATCH':
        try:
            async_generate_campaign.delay(store_id, page_id)
        except socket_error as serr:
            if serr.errno != errno.ECONNREFUSED:
                # If we wanted to do something if rabbit is not running locally,
                # this is where we would put it.
                pass

        r = ContentGraphClient.store(store_id).page(page_id).PATCH(data=request.body)

    return mimic_response(r)
