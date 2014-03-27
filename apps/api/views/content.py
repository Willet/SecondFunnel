import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from apps.api.paginator import BaseCGHandler, BaseItemCGHandler
from apps.assets.models import Content, Store, Page
from apps.intentrank.utils import ajax_jsonp


class ContentItemCGHandler(BaseItemCGHandler):
    model = Content
    id_attr = 'content_id'  # the arg in the url pattern used to select something


class ContentCGHandler(BaseCGHandler):
    model = Content
    id_attr = 'content_id'  # the arg in the url pattern used to select something


class StoreContentCGHandler(ContentCGHandler):
    """Adds filtering by store"""
    store = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        self.store = get_object_or_404(Store, id=store_id)

        return super(StoreContentCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreContentCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store.id)


class StoreContentItemCGHandler(ContentCGHandler):
    """Adds filtering by store"""
    store = None
    content_id = None  # old ID
    id_attr = 'content_id'

    def get(self, request, *args, **kwargs):
        return ajax_jsonp(self.serialize_one())

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        self.store = get_object_or_404(Store, id=store_id)
        self.content_id = kwargs.get(self.id_attr)

        return super(StoreContentItemCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreContentItemCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store.id,
                         id=self.content_id)


class StorePageContentCGHandler(StoreContentCGHandler):
    """Adds filtering by page/feed"""
    feed = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, id=page_id)
        self.feed = page.feed

        return super(StorePageContentCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        """get all the contents in the feed, which is
        all the feed's tiles' contents
        """
        tile_content_ids = self.feed.tiles.values_list('content__id', flat=True)
        contents = Content.objects.filter(id__in=tile_content_ids)
        return contents


class StorePageContentItemCGHandler(StoreContentItemCGHandler):
    """Adds filtering by page/feed"""
    feed = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, id=page_id)
        self.feed = page.feed

        return super(StoreContentItemCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        """get all the contents in the feed, which is
        all the feed's tiles' contents
        """
        tiles = self.feed.tiles.all()
        contents = []
        for tile in tiles:
            contents += tile.content.all()
        return contents


class StorePageContentSuggestedCGHandler(StorePageContentCGHandler):
    """GET only; compute list of content based on products on page."""
    def get_queryset(self, request=None):
        """get all the contents in the feed, which is
        all the feed's tiles' contents
        """
        store = self.store

        # find ids of content not already present in the current set of tiles
        tile_content_ids = self.feed.tiles.values_list('content__id', flat=True)
        not_in_feed = list(set(store.content.values_list('id', flat=True)) -
                           set(tile_content_ids))

        # mass select and initialize these content models
        not_in_feed = (Content.objects.filter(id__in=not_in_feed)
                                      .select_subclasses())

        return not_in_feed

    def post(self, request, *args, **kwargs):
        raise NotImplementedError()
    put = patch = delete = post


class StorePageContentTagCGHandler(StorePageContentItemCGHandler):
    """Supports content tagging

    GET content id: list tagged product ids on that product
    POST content id with product id: add (not replace) that product tag
                                     returns updated content
    DELETE content id with product id: remove that product tag
                                       returns updated content

    All other operations: not supported
    """
    content = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        content_id = kwargs.get('content_id')
        try:
            self.content = Content.objects.filter(id=content_id).select_subclasses()[0]
        except ObjectDoesNotExist:
            raise Http404()

        return super(StorePageContentTagCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        return Content.objects.filter(id=request).select_subclasses()

    def get(self, request, *args, **kwargs):
        return ajax_jsonp({
            'results': [x.id for x in self.content.tagged_products.all()]
        })

    def post(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        tagged_product_ids = self.content.tagged_products.values_list('id', flat=True)
        if not product_id in tagged_product_ids:
            tagged_product_ids.append(product_id)

        self.content.update({'tagged_products': tagged_product_ids})
        self.content.save()
        return ajax_jsonp(self.content.to_cg_json())

    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        tagged_product_ids = self.content.tagged_products.values_list('id', flat=True)
        try:
            # remove all instances of product_id
            tagged_product_ids = [i for i in tagged_product_ids if i != product_id]
        except IndexError:
            pass

        self.content.update({'tagged_products': tagged_product_ids})
        self.content.save()
        return ajax_jsonp(self.content.to_cg_json())

    def put(self, request, *args, **kwargs):
        raise NotImplementedError()

    def patch(self, request, *args, **kwargs):
        raise NotImplementedError()


class PageContentAllCGHandler(StorePageContentCGHandler):
    """PUT adds all content specified in the request body to the page.

    No other HTTP verb is supported.

    This view is identical to PageProductAllCGHandler.
    """
    def get(self, request, *args, **kwargs):
        raise NotImplementedError()

    def put(self, request, *args, **kwargs):
        """:returns 200"""
        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, id=page_id)

        content_ids = json.loads(request.body)
        contents = Content.objects.filter(id__in=content_ids).select_subclasses()
        for content in contents:
            page.add_content(content)

        return HttpResponse()

    post = patch = delete = get
