import json

from django.shortcuts import get_object_or_404

from apps.api.paginator import BaseCGHandler
from apps.assets.models import Product, Store, Page
from apps.intentrank.utils import ajax_jsonp


class ProductCGHandler(BaseCGHandler):
    model = Product
    id_attr = 'product_id'


class StoreProductsCGHandler(ProductCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, old_id=store_id)
        self.store_id = store.id

        return super(StoreProductsCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreProductsCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id)


class StoreProductCGHandler(ProductCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID
    product_id = None  # old ID

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, old_id=store_id)
        self.store_id = store.id
        self.product_id = kwargs.get('product_id')

        return super(StoreProductCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreProductCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id,
                         old_id=self.product_id)


class StorePageProductCGHandler(StoreProductsCGHandler):
    """Adds filtering by page/feed"""
    feed = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, old_id=page_id)
        self.feed = page.feed

        return super(StoreProductsCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        """get all the products in the feed, which is
        all the feed's tiles' products
        """
        tiles = self.feed.tiles.all()
        products = []
        for tile in tiles:
            products += tile.products.all()
        return products
