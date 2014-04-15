import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.decorators import check_login, request_methods
from apps.api.paginator import BaseCGHandler, BaseItemCGHandler
from apps.assets.models import Page, Store, Feed, Theme
from apps.intentrank.utils import ajax_jsonp
from apps.static_pages.views import (generate_static_campaign,
                                     transfer_static_campaign)


class PageCGHandler(BaseCGHandler):
    model = Page


class PageItemCGHandler(BaseItemCGHandler):
    model = Page


class StorePageCGHandler(PageCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, id=store_id)
        self.store = store
        self.store_id = store.id

        return super(StorePageCGHandler, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Creates a Page.

        In reality, creates a page, a feed, and associations among them
        and their store.
        """
        print "StorePageCGHandler handling POST {0}".format(request.path)
        data = json.loads(request.body)
        new_feed = Feed()
        new_feed.save()

        new_theme = Theme()
        new_theme.save()

        new_page = self.model()
        new_page.store = self.store
        new_page.feed = new_feed
        new_page.theme = new_theme
        new_page.url_slug = data['url']
        new_page.update(data)

        new_page.save()  # :raises ValidationError
        return ajax_jsonp(new_page.to_cg_json())

    def get_queryset(self, request=None):
        qs = super(StorePageCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id)


class StorePageItemCGHandler(PageItemCGHandler):
    """Adds filtering by store"""
    model = Page
    id_attr = 'page_id'
    page_id = None
    store_id = None  # new ID

    def get(self, request, *args, **kwargs):
        return ajax_jsonp(self.serialize_one())

    def patch(self, request, *args, **kwargs):
        print "StorePageItemCGHandler handling PATCH {0}".format(request.path)
        page_id = kwargs.get(self.id_attr)
        if not page_id:
            raise HttpResponse(status=405)  # url didn't capture what to delete

        data = json.loads(request.body)
        if 'theme' in data:
            # it is guaranteed when you PATCH that the theme is created
            data['theme'] = Theme.objects.filter(template=data['theme']).last()

        page = get_object_or_404(self.model, id=page_id)
        page.update(**data)
        page.save()
        return ajax_jsonp(page.to_cg_json())
    
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]

        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, id=page_id)
        self.page_id = page.id

        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, id=store_id)
        self.store_id = store.id

        return super(StorePageItemCGHandler, self).dispatch(*args, **kwargs)
    
    def get_queryset(self, request=None):
        qs = super(StorePageItemCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id, id=self.page_id)


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
