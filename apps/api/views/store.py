import json

from django.shortcuts import get_object_or_404

from apps.api.paginator import BaseCGHandler, BaseItemCGHandler
from apps.assets.models import Store
from apps.intentrank.utils import ajax_jsonp


class StoreCGHandler(BaseCGHandler):
    model = Store

    def get(self, request, *args, **kwargs):
        stores = self.model.objects.all()

        store_id = kwargs.get('store_id', request.GET.get('store_id'))
        if store_id:
            stores = stores.filter(id=store_id)
        slug = kwargs.get('slug', request.GET.get('slug'))
        if kwargs.get('slug', slug):
            stores = stores.filter(slug=slug)

        self.object_list = stores

        return ajax_jsonp(self.serialize())


class StoreItemCGHandler(BaseItemCGHandler):
    model = Store

    def get(self, request, *args, **kwargs):
        stores = self.model.objects.all()

        store_id = kwargs.get('store_id', request.GET.get('store_id'))
        if store_id:
            stores = stores.filter(id=store_id)
        slug = kwargs.get('slug', request.GET.get('slug'))
        if kwargs.get('slug', slug):
            stores = stores.filter(slug=slug)

        self.object_list = stores

        return ajax_jsonp(self.serialize_one())