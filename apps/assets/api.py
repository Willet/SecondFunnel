from tastypie import fields
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import BasicAuthentication
from django.db.models import Q

from apps.assets.models import Product, Store, ProductMedia


class StoreResource(ModelResource):
    class Meta:
        queryset = Store.objects.all()
        resource_name = 'store'
        authentication = BasicAuthentication()


class ProductResource(ModelResource):
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        queryset = Product.objects.all()
        resource_name = 'product'

        filtering = {
            'store': ALL,
            'name': ('exact', 'contains',),
            'name_or_url': ('exact')
        }
        authentication = BasicAuthentication()

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(ProductResource, self).build_filters(filters)

        if('name_or_url' in filters):
            name = filters['name_or_url']
            qset = (
                Q(name__contains=name) |
                Q(original_url__startswith=name)
            )
            orm_filters.update({'name_or_url': qset})

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        if 'name_or_url' in applicable_filters:
            custom = applicable_filters.pop('name_or_url')
            # we only want to filter by the custom filters so don't apply any filters here
            applicable_filters = {}
        else:
            custom = None

        semi_filtered = super(ProductResource, self).apply_filters(request, applicable_filters)

        return semi_filtered.filter(custom) if custom else semi_filtered


class ProductMediaResource(ModelResource):
    product = fields.ForeignKey(ProductResource, 'product')

    class Meta:
        queryset = ProductMedia.objects.all()
        resource_name = 'product_media'

        filtering = {
            'product': ALL
        }
        authentication = BasicAuthentication()
