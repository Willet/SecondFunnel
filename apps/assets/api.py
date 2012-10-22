from tastypie import fields
from tastypie.resources import ModelResource, ALL

from apps.assets.models import Product, Store, ProductMedia


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
            'original_url': ('exact', 'startswith',),
            'name': ('exact', 'contains',)
        }


class ProductMediaResource(ModelResource):
    product = fields.ForeignKey(ProductResource, 'product')

    class Meta:
        queryset = ProductMedia.objects.all()
        resource_name = 'product_media'

        filtering = {
            'product': ALL
        }
