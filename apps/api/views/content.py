import json

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query_utils import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from apps.api.paginator import BaseCGHandler, BaseItemCGHandler
from apps.assets.models import Content, Store, Page, ProductImage, Product, Image, Video
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
        qs = qs.filter(store_id=self.store.id)

        if request.GET.get('status', ''):
            qs = qs.filter(status=request.GET.get('status'))

        if request.GET.get('source', ''):
            qs = qs.filter(source=request.GET.get('source'))

        # search by what the UI refers to as "tags"
        tagged_products = request.GET.get('tagged-products', '')
        if tagged_products:
            qs = qs.filter(Q(tagged_products__name__icontains=tagged_products) |
                           Q(tagged_products__description__icontains=tagged_products))

        # search by what the UI refers to as "type"
        # this is an EXPENSIVE operation!
        content_type = request.GET.get('type', '')
        if content_type:
            if content_type == 'image':
                qs = [x for x in qs.select_subclasses() if isinstance(x, Image)]
            elif content_type == 'video':
                qs = [x for x in qs.select_subclasses() if isinstance(x, Video)]
        return qs

class StoreContentItemCGHandler(ContentItemCGHandler):
    """Adds filtering by store"""
    store = None
    content_id = None
    content = None
    id_attr = 'content_id'

    def get(self, request, *args, **kwargs):
        # this handler needs to return either
        content = Content.objects.filter(store=self.store).select_subclasses()
        product_ids = Product.objects.filter(store=self.store).values_list('id', flat=True)
        product_images = ProductImage.objects.filter(product_id__in=product_ids)

        content_id = kwargs.get('content_id', request.GET.get('content_id'))
        if content_id:
            content = content.filter(id=content_id)
            product_images = product_images.filter(id=content_id)

        if product_images.count():
            self.object_list = product_images
        else:
            self.object_list = content

        if not self.object_list:
            raise Http404()

        return ajax_jsonp(self.serialize_one())

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        self.store = get_object_or_404(Store, id=store_id)
        self.content_id = kwargs.get(self.id_attr)

        if kwargs.get('content_id'):
            try:
                self.content = Content.objects.get(id=kwargs.get('content_id'))
            except Content.DoesNotExist:
                self.content = get_object_or_404(ProductImage,
                                                 id=kwargs.get('content_id'))

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
        content_id = kwargs.get('content_id')
        page = get_object_or_404(Page, id=page_id)
        try:
            self.content = Content.objects.filter(id=content_id).select_subclasses()[0]
        except ObjectDoesNotExist:
            raise Http404()

        self.page = page
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

    def put(self, request, *args, **kwargs):
        """special handler for adding a content to the page"""
        self.page.add_content(self.content)
        return ajax_jsonp(self.content.to_cg_json())

    def delete(self, request, *args, **kwargs):
        """special handler for deleting a content from the page
        (which means adding a content to a tile to the feed of the page)
        """
        self.page.delete_content(self.content)
        return ajax_jsonp(self.content)


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


class StoreContentStateItemCGHandler(ContentItemCGHandler):
    """Approves/Unapproves/Undecides a piece of content, depending on class name"""
    def post(self, request, *args, **kwargs):
        raise NotImplementedError()

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        self.store = get_object_or_404(Store, id=store_id)
        self.content_id = kwargs.get(self.id_attr)

        # can't tag ProductImage classes, which is fine for this set of
        # API urls
        try:
            self.content = Content.objects.filter(id=content_id).select_subclasses()[0]
        except ObjectDoesNotExist:
            raise Http404()

        return super(StoreContentStateItemCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreContentStateItemCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store.id,
                         id=self.content_id)


class StoreContentApproveItemCGHandler(StoreContentStateItemCGHandler):
    """Approves a piece of content"""
    def post(self, request, *args, **kwargs):
        self.content.status = "approved"
        self.content.save()
        return ajax_jsonp(self.content)


class StoreContentRejectItemCGHandler(StoreContentStateItemCGHandler):
    """Rejects a piece of content (not that it has any effect)"""
    def post(self, request, *args, **kwargs):
        self.content.status = "rejected"
        self.content.save()
        return ajax_jsonp(self.content)


class StoreContentUndecideItemCGHandler(StoreContentStateItemCGHandler):
    """Since the new default value is "approved", this status is actually
    discouraged.
    """
    def post(self, request, *args, **kwargs):
        self.content.status = "needs-review"
        self.content.save()
        return ajax_jsonp(self.content)


class StorePageContentPrioritizeItemCGHandler(StorePageContentItemCGHandler):
    def post(self, request, *args, **kwargs):

        feed = self.page.feed
        tiles_with_this_content = feed.find_tiles(content=self.content)
        if len(tiles_with_this_content):  # tile is already in the feed
            for tile in tiles_with_this_content:
                print "prioritized tile {0} for content {1}".format(
                    tile.id, self.content.id)
                tile.prioritized = "pageview"
                tile.save()
        else:  # tile not in the feed, create a prioritized tile
            self.page.add_content(content=self.content, prioritized='pageview')

        return ajax_jsonp(self.content.to_cg_json())

    def get(self, request, *args, **kwargs):
        raise NotImplementedError()
    put = patch = delete = get


class StorePageContentDeprioritizeItemCGHandler(StorePageContentItemCGHandler):
    """Finds the tile with this content in the feed that belongs to this page
    and deprioritises it.
    """
    def post(self, request, *args, **kwargs):

        feed = self.page.feed
        tiles_with_this_content = feed.find_tiles(content=self.content)
        for tile in tiles_with_this_content:
            print "prioritized tile {0} for content {1}".format(
                tile.id, self.content.id)
            tile.prioritized = ""
            tile.save()

        return ajax_jsonp(self.content.to_cg_json())

    def get(self, request, *args, **kwargs):
        raise NotImplementedError()
    put = patch = delete = get


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
