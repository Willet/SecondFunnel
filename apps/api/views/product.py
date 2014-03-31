import json
from django.http import HttpResponse

from django.shortcuts import get_object_or_404

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

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, id=store_id)
        self.store_id = store.id

        return super(StoreProductCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreProductCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id)


class StoreProductItemCGHandler(ProductCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID
    product_id = None  # old ID

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


class StorePageProductPrioritizeItemCGHandler(StorePageProductItemCGHandler):
    def post(self, request, *args, **kwargs):

        feed = self.page.feed
        tiles_with_this_product = feed.find_tiles(self.product)
        for tile in tiles_with_this_product:
            tile.prioritized = True
            tile.save()

        return HttpResponse()

    def get(self, request, *args, **kwargs):
        raise NotImplementedError()
    put = patch = delete = get


class StorePageProductDeprioritizeItemCGHandler(StorePageProductItemCGHandler):
    """Finds the tile with this product in the feed that belongs to this page
    and deprioritises it.
    """
    def post(self, request, *args, **kwargs):

        feed = self.page.feed
        tiles_with_this_product = feed.find_tiles(self.product)
        for tile in tiles_with_this_product:
            tile.prioritized = False
            tile.save()

        return HttpResponse()

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
