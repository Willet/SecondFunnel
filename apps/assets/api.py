from django.contrib.auth.models import User
from django.db.models.signals import post_save
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.fields import ForeignKey
from tastypie.models import ApiKey
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import Authentication, ApiKeyAuthentication, MultiAuthentication
from tastypie.authorization import Authorization
from django.db.models import Q

from apps.assets.models import (Product, Store)

from apps.pinpoint.models import Campaign, StoreTheme


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
    """REST-style store."""
    class Meta:
        queryset = Store.objects.all()
        resource_name = 'store'
        authentication = UserAuthentication()
        authorization = UserPartOfStore()
        filtering = {
            'id': ('exact',),
            'name': ('icontains',),
        }


class StoreThemeResource(ModelResource):
    """REST-style store themes of the current user's store."""
    class Meta:
        queryset = StoreTheme.objects.all()
        resource_name = 'store_theme'
        authentication = ApiKeyAuthentication()
        authorization= Authorization()

    def _get_store_staff(self, request):
        """get a {store: [users]} map."""
        stores = {}
        for store in Store.objects.all():
            stores[store] = store.staff.all()
        return stores

    def apply_authorization_limits(self, request, object_list):
        user_store_ids = []  # list of id of stores that this user can access
        for store, users in self._get_store_staff(request):
            if request.user in users:
                user_store_ids.append(store.id)
        return object_list.filter(store_id__in=user_store_ids)


class ProductResource(ModelResource):
    """REST (tastypie) version of a Product."""
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        """Django's way of defining a model's metadata."""
        queryset = Product.objects.all()
        resource_name = 'product'

        filtering = {
            'store': ALL,
            'id': ('exact',),
            'name': ('exact', 'contains',),
            'name_or_url': ('exact'),
            'available': ('exact'),
        }
        authentication = UserAuthentication()
        authorization = UserPartOfStore()

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
        else:
            availability = True
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


class CampaignResource(ModelResource):
    """Returns "a campaign".

    Campaign definitions are saved in apps/pinpoint/models.py.
    """
    store = fields.ForeignKey(StoreResource, 'store', full=True)

    class Meta:
        queryset = Campaign.objects.all()
        resource_name = 'campaign'

        filtering = {
            'store': ALL,
        }


# Apparently, create_api_key only creates on user creation
# Resolve this by creating a key if the key doesn't exist.
def get_or_create_api_key(sender, **kwargs):
    user = kwargs.get('instance')

    if not user:
        return

    ApiKey.objects.get_or_create(user=user)


# signals
post_save.connect(get_or_create_api_key, sender=User)
