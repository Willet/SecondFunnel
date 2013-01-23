from tastypie import fields
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from apps.assets.models import Product, Store, ProductMedia


class UserAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        return request.user.is_authenticated()


class UserPartOfStore(Authorization):
    def is_authorized(self, request, object=None):
        try:
            if request.user in Store.objects.get(id=request.GET['store']).staff.all():
                return True
            else:
                return False
        except (KeyError, ValueError, Store.DoesNotExist):
            return False


class StoreResource(ModelResource):
    class Meta:
        queryset = Store.objects.all()
        resource_name = 'store'
        authentication = UserAuthentication()
        authorization = UserPartOfStore()


class ProductResource(ModelResource):
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        queryset = Product.objects.all()
        resource_name = 'product'

        filtering = {
            'store': ALL,
            'id': ('exact',),
            'name': ('exact', 'contains',),
            'name_or_url': ('exact')
        }
        authentication = UserAuthentication()
        authorization = UserPartOfStore()

    def get_object_list(self, request):
        result = super(ProductResource, self).get_object_list(request)
        if 'store' in request.GET:
            return result.filter(store=request.GET['store'])
        else:
            return result.none()

    def build_filters(self, filters=None):
        if filters is None:
            filters = {}

        orm_filters = super(ProductResource, self).build_filters(filters)

        if('name_or_url' in filters):
            name = filters['name_or_url']
            qset = (
                Q(name__icontains=name) |
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
        authentication = UserAuthentication()
        authorization = UserPartOfStore()
