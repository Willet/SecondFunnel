from tastypie import fields
from tastypie.resources import ModelResource, ALL

from apps.assets.models import Product, Store


class StoreResource(ModelResource):
    class Meta:
        queryset = Store.objects.all()
        resource_name = 'store'


class ProductResource(ModelResource):
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        queryset = Product.objects.all()
        resource_name = 'product'

        filtering = {
            'store': ALL,
            'original_url': ('exact', 'startswith',)
        }
