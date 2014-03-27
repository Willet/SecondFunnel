import json

from django.shortcuts import get_object_or_404

from apps.api.paginator import BaseCGHandler
from apps.assets.models import Store
from apps.intentrank.utils import ajax_jsonp


class StoreCGHandler(BaseCGHandler):
    model = Store

    def get(self, request, *args, **kwargs):
        if kwargs.get('store_id'):
            self.object_list = get_object_or_404(self.model, id=kwargs.get('store_id'))
        else:
            self.object_list = Store.objects.all()

        return ajax_jsonp(self.serialize())
