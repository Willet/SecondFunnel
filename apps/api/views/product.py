import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse

from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.api.paginator import BaseCGHandler, BaseItemCGHandler
from apps.assets.models import Product, Store, Page
from apps.intentrank.utils import ajax_jsonp


class ProductCGHandler(BaseCGHandler):
    model = Product
    id_attr = 'product_id'


class ProductItemCGHandler(BaseItemCGHandler):
    model = Product
    id_attr = 'product_id'


class StoreProductCGHandler(ProductCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, id=store_id)
        self.store_id = store.id

        return super(StoreProductCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreProductCGHandler, self).get_queryset()
        qs = qs.filter(store_id=self.store_id)

        # filtering for the select2 tagging
        # or
        # filtering for page manager
        search_name = request.GET.get('search-name', '') or \
                      request.GET.get('tags', '')
        if search_name:
            # if search present, search in name or description
            qs = qs.filter(Q(name__icontains=search_name) |
                           Q(description__icontains=search_name))

        return qs.filter(store_id=self.store_id)


class StoreProductItemCGHandler(ProductItemCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID
    product_id = None  # old ID

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, id=store_id)
        self.store_id = store.id
        self.product_id = kwargs.get('product_id')

        return super(StoreProductItemCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreProductItemCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id,
                         id=self.product_id)


class StorePageProductCGHandler(StoreProductCGHandler):
    """Adds filtering by page/feed"""
    feed = None

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, id=page_id)
        self.feed = page.feed

        return super(StoreProductCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        """get all the products in the feed, which is
        all the feed's tiles' products
        """
        tiles = self.feed.tiles.all()
        products = []
        for tile in tiles:
            products += tile.products.all()
        return products


class StorePageProductItemCGHandler(StoreProductItemCGHandler):
    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        product_id = kwargs.get('product_id')
        page = get_object_or_404(Page, id=page_id)
        product = get_object_or_404(Product, id=product_id)
        self.page = page
        self.product = product

        return super(StorePageProductItemCGHandler, self).dispatch(*args, **kwargs)

    def put(self, request, *args, **kwargs):
        """special handler for adding a product to the page"""
        self.page.add_product(self.product)
        return ajax_jsonp(self.product.to_cg_json())

    def delete(self, request, *args, **kwargs):
        """special handler for deleting a product from the page
        (which means adding a product to a tile to the feed of the page)
        """
        self.page.delete_product(self.product)
        return ajax_jsonp(self.product)


class StorePageProductPrioritizeItemCGHandler(StorePageProductItemCGHandler):
    def post(self, request, *args, **kwargs):

        feed = self.page.feed
        tiles_with_this_product = feed.find_tiles(product=self.product)
        for tile in tiles_with_this_product:
            print "prioritized tile {0} for product {1}".format(
                tile.id, self.product.id)
            tile.prioritized = "pageview"
            tile.save()

        return ajax_jsonp(self.product.to_cg_json())

    def get(self, request, *args, **kwargs):
        raise NotImplementedError()
    put = patch = delete = get


class StorePageProductDeprioritizeItemCGHandler(StorePageProductItemCGHandler):
    """Finds the tile with this product in the feed that belongs to this page
    and deprioritises it.
    """
    def post(self, request, *args, **kwargs):

        feed = self.page.feed
        tiles_with_this_product = feed.find_tiles(product=self.product)
        if len(tiles_with_this_product):  # tile is already in the feed
            for tile in tiles_with_this_product:
                print "prioritized tile {0} for product {1}".format(
                    tile.id, self.product.id)
                tile.prioritized = ""
                tile.save()
        else:  # tile not in the feed, create a prioritized tile
            self.page.add_product(product=self.product, prioritized='pageview')

        return ajax_jsonp(self.product.to_cg_json())

    def get(self, request, *args, **kwargs):
        raise NotImplementedError()
    put = patch = delete = get


class PageProductAllCGHandler(StorePageProductCGHandler):
    """PUT adds all products specified in the request body to the page.

    No other HTTP verb is supported.

    This view is identical to PageProductAllCGHandler.
    """
    def get(self, request, *args, **kwargs):
        raise NotImplementedError()

    def put(self, request, *args, **kwargs):
        """:returns 200"""
        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, id=page_id)

        product_ids = json.loads(request.body)
        for product_id in product_ids:
            product = get_object_or_404(Product, id=product_id)
            page.add_product(product)

        return HttpResponse()

    post = patch = delete = get
