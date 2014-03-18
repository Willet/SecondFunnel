import json

from django.shortcuts import get_object_or_404

from apps.api.paginator import BaseCGHandler
from apps.assets.models import Product, Store, Page


class ProductCGHandler(BaseCGHandler):
    model = Product

    def patch(self, request, *args, **kwargs):
        product = get_object_or_404(self.model, old_id=kwargs.get('product_id'))
        product.update(**json.loads(request.body))
        product.save()
        return product.to_cg_json()


class StoreProductCGHandler(ProductCGHandler):
    """Adds filtering by store"""
    store_id = None  # new ID

    def dispatch(self, *args, **kwargs):
        request = args[0]
        store_id = kwargs.get('store_id')
        store = get_object_or_404(Store, old_id=store_id)
        self.store_id = store.id

        return super(StoreProductCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        qs = super(StoreProductCGHandler, self).get_queryset()
        return qs.filter(store_id=self.store_id)


class StorePageProductCGHandler(StoreProductCGHandler):
    """Adds filtering by page/feed"""
    feed = None

    def dispatch(self, *args, **kwargs):
        request = args[0]
        page_id = kwargs.get('page_id')
        page = get_object_or_404(Page, old_id=page_id)
        self.feed = page.feed

        return super(StoreProductCGHandler, self).dispatch(*args, **kwargs)

    def get_queryset(self, request=None):
        """get all the products in the feed, which is
        all the feed's tiles' products
        """
        tiles = self.feed.tiles.all()
        products = []
        for tile in tiles:
            products += tile.product.all()
        return products
