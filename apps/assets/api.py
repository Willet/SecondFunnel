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
    """REST (tastypie) version of a Product."""
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        """Django's way of defining a model's metadata."""
        queryset = Product.objects.all()
        resource_name = 'product'

        filtering = {
            'store': ALL,
            'name': ('exact', 'contains',),
            'name_or_url': ('exact'),
            'available': ('exact'),
        }
        authentication = UserAuthentication()
        authorization = UserPartOfStore()

    def get_object_list(self, request):
        """Extended defined function from ModelResource in tastypie."""
        result = super(ProductResource, self).get_object_list(request)
        if 'store' in request.GET:
            return result.filter(store=request.GET['store'])
        else:
            return result.none()

    def build_filters(self, filters=None):
        """build_filters (transitions) resource lookup to an ORM lookup.

        Also an extended defined function from ModelResource in tastypie.
        """
        if filters is None:
            filters = {}

        orm_filters = super(ProductResource, self).build_filters(filters)

        if('name_or_url' in filters):
            name = filters['name_or_url']
            qset = (
                Q(name__icontains=name) |
                Q(original_url__startswith=name)
            )
            # add a filter that says "name or url contains (name)"
            orm_filters.update({'name_or_url': qset})

        availability = filters.get('available', True)
        if availability == 'False':
            availability = False
        qset = (Q(available=availability))
        orm_filters.update({'available': qset})

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        """Excludes filters that are not exactly a field in the database schema
        and do them elsewhere.

        TODO: I think the logic is flawed, but I can't explain why.
        """
        custom = []
        custom_filters = ['name_or_url', 'available']

        for filter_ in custom_filters:  # filter is a function
            if filter_ in applicable_filters:
                # we only want to filter by the custom filters
                # so don't apply any filters here
                custom.append(applicable_filters.pop(filter_))

        # apply primitive filters
        semi_filtered = super(ProductResource, self).apply_filters(
            request, applicable_filters)

        # apply our crazier ones
        for custom_filter in custom:
            semi_filtered = semi_filtered.filter(custom_filter)

        return semi_filtered


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
