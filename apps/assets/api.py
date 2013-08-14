from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.urlresolvers import reverse
from django.conf.urls import url
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.models import ApiKey
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import Authentication, ApiKeyAuthentication, MultiAuthentication
from tastypie.authorization import Authorization
from django.db.models import Q

from apps.assets.models import (Product, Store, ProductMedia, ExternalContent,
    YoutubeVideo, GenericImage, ExternalContent, ExternalContentType)

from apps.pinpoint.models import BlockContent, Campaign, StoreTheme
from apps.assets.api_utils import PrettyJSONSerializer


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


class FilteredModelResource(ModelResource):
    """A subclass of a ModelResource to attempt to make API filtering easier by
    reducing the amount of redundant code."""
    class Meta:
        custom_filtering = {
            """
            A mapping that takes tuple a tuple.  Any strings in a tuple together are considered
            ANDs, tuples seperated by commas are considered ORs.
            """
        }

    def dehydrate(self, bundle):
        """Add username to the bundle data, so that API calls with username passed as a GET
        param can succeed.

        @param bundle: An object representing values needed to build the resource.
        @return: bundle"""
        if hasattr(bundle.obj, 'username'):
            bundle.data['username'] = bundle.obj.username
        return super(FilteredModelResource, self).dehydrate(bundle)

    def evaluate_queryset(self, query_string, qset):
        """Evaluates the passed query set to determine what query it represents (series of ANDs and
        ORs) using the passed query string as the value to create the Q object.

        @param query_string: The value to pass to the Q object.
        @param qset: A tuple of arguments to construct the necessary Q objects.
        @return: Q
        """
        query_object = None

        for qs in qset:
            # Iterate over the querystrings
            if isinstance(qs, tuple):
                # Assume a tuple is an OR
                qs = self.evaluate_queryset(query_string, qs)
                query_object = query_object | qs if query_object else qs
            else:
                # Assume a string is an AND (default)
                query = query_string

                if qs.endswith('in'):
                    query = query.split(',')
                elif qs.endswith('range'):
                    query = query.split('-')
                    start, end = query[:len(query)/2], query[len(query)/2:]
                    query = ("-".join(start), "-".join(end))

                if qs.startswith('~'):
                    qs = ~Q(**{qs[1:]:query})
                else:
                    qs = Q(**{qs:query})

                query_object  = query_object & qs if query_object else qs

        return query_object

    def build_filters(self, filters=None):
        """Builds a list of filters using the custom filters and the ModelResource
        filters as defined by the Meta.filtering.

        @param filters: QueryDict of filters to use.
        @return: dict
        """
        filters = filters or {}
        custom_filters = self.Meta.custom_filtering
        non_custom_filters, custom = {}, {}

        for _filter in filters:
            if not _filter in custom_filters:
                non_custom_filters[_filter] = filters[_filter]
            else:
                custom[_filter] = filters[_filter]

        orm_filters = super(FilteredModelResource, self).build_filters(non_custom_filters)

        for _filter in custom:
            qs = self.evaluate_queryset(filters[_filter], custom_filters[_filter])
            orm_filters.update({_filter: qs})

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        """Apply the filters by seperating the custom ones from the non-custom ones; custom
        ones are applied seperately (expected to be Q objects).

        @param request: The user request object
        @param applicable_filters: A dict of filters to be applied.
        @return: object or list of objects
        """
        custom_filters = self.Meta.custom_filtering
        custom = []

        for _filter in applicable_filters.keys():
            if isinstance(applicable_filters[_filter], Q) or \
                    _filter in custom_filters:
                custom.append(applicable_filters.pop(_filter))

        semi_filtered = super(FilteredModelResource, self).apply_filters(request, applicable_filters)
        for _filter in custom:
            semi_filtered = semi_filtered.filter(_filter)

        return semi_filtered


class BlockContentResource(ModelResource):
    """Returns a campaign's content blocks."""
    class Meta:
        queryset = BlockContent.objects.all()
        resource_name = 'block_content'

    def dehydrate(self, bundle):
        """convert BlockContent.data to something meaningful."""
        # http://django-tastypie.readthedocs.org/en/latest/bundles.html
        data_type = bundle.obj.data

        fields = data_type._meta.fields
        bundle.data['data'] = {}
        for field in fields:
            bundle.data['data'][field.name] = getattr(data_type, field.name,
                                                      None)

        return bundle


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


class StoreThemeResource(FilteredModelResource):
    """Returns a "store theme".

    Store theme definitions are saved in apps/pinpoint/models.py.
    """
    class Meta:
        queryset = StoreTheme.objects.all()
        resource_name = 'store_theme'
        serializer = PrettyJSONSerializer()
        authentication = MultiAuthentication(
            ApiKeyAuthentication(),
            UserAuthentication())
        authorization = UserPartOfStore()
        custom_filtering = {
            'store': ('store__id__exact',),
            'store_name': ('store__name__iexact',),
            'name': ('name__icontains',),
        }

        filtering = {
            'store': ALL_WITH_RELATIONS,
            'name': ('exact',),
        }

    def dehydrate(self, bundle):
        stores = Store.objects.filter(Q(theme=bundle.obj) | Q(mobile=bundle.obj))
        campaigns = Campaign.objects.filter(Q(theme=bundle.obj) | Q(mobile=bundle.obj) | 
                                            Q(store__in=stores))

        for key, objs in zip(['stores', 'campaigns'], [stores, campaigns]):
            if not key in bundle.data:
                bundle.data[key] = []
            for obj in objs:
                bundle.data[key].append({
                    'id': obj.id,
                    'name': obj.name,
                    'resource_uri': reverse('api_dispatch_detail', kwargs={
                        'resource_name': key[:-1], 
                        'api_name': 'v1', 
                        'pk': obj.id
                    })
                })

        return super(StoreThemeResource, self).dehydrate(bundle)

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/store/(?P<store>[\w\d_.:\-\s]+)/$"% self._meta.resource_name,
                self.wrap_view('dispatch_store_themes'), name="api_dispatch_store_themes"),
        ]

    def dispatch_store_themes(self, request, **kwargs):
        """Attempts to find the related store and return all the themes associated with that store.
        Returns a HttpResponse corresponding to the API call.

        @param request: The request object.
        @return: HttpResponse
        """
        try:
            store = Store.objects.get(name__iexact=kwargs['store'])
            kwargs['store'] = store.id
        except Store.DoesNotExist:
            pass

        return super(StoreThemeResource, self).dispatch_list(request, **kwargs)


class CampaignResource(ModelResource):
    """Returns "a campaign".

    Campaign definitions are saved in apps/pinpoint/models.py.
    """
    store = fields.ForeignKey(StoreResource, 'store', full=True)
    content_blocks = fields.ToManyField(BlockContentResource, 'content_blocks',
                                        full=True)
    discovery_blocks = fields.ToManyField(BlockContentResource,
                                          'discovery_blocks', full=True)
    theme = fields.ForeignKey(StoreThemeResource, 'store_theme', blank=True, null=True)
    mobile_theme = fields.ForeignKey(StoreThemeResource, 'mobile_store_theme', blank=True, null=True)

    class Meta:
        queryset = Campaign.objects.all()
        resource_name = 'campaign'
        serializer = PrettyJSONSerializer()

        filtering = {
            'store': ALL,
        }

    def dehydrate(self, bundle):
        id = bundle.data['store'].data['id']
        store = Store.objects.get(pk=id)

        for key, theme in zip(['theme', 'mobile_theme'], 
                              [store.theme_id, store.mobile_id]):
            if not bundle.data[key] and theme:
                theme = StoreTheme.objects.get(pk=theme)
                bundle.data[key] = {
                    'id': theme.id,
                    'name': theme.name,
                    'resource_uri': reverse('api_dispatch_detail', kwargs={
                        'pk': theme.id, 
                        'resource_name': "store_theme", 
                        'api_name': 'v1'
                    })
                }

        return super(CampaignResource, self).dehydrate(bundle)


class YoutubeVideoResource(ModelResource):
    """Access to youtube video model"""

    class Meta:
        queryset = YoutubeVideo.objects.all()
        authentication = UserAuthentication()
        resource_name = 'youtube_video'

        filtering = {
            'id': ('exact',)
        }


class GenericImageResource(ModelResource):
    """Access to GenericImage model"""

    class Meta:
        queryset = GenericImage.objects.all()
        authentication = UserAuthentication()
        resource_name = 'generic_image'

        filtering = {
            'id': ('exact',)
        }


class ExternalContentTypeResource(ModelResource):
    """Access to list of content types"""

    class Meta:
        queryset = ExternalContentType.objects.all()
        authentication = UserAuthentication()
        authorization= Authorization()
        resource_name = 'external_content_type'


class ExternalContentResource(ModelResource):
    """Access to ExternalContent model"""

    products = fields.ManyToManyField(ProductResource, 'tagged_products',
        null=True, full=False, related_name='external_content')

    type = fields.ForeignKey(ExternalContentTypeResource, 'content_type',
                             full=True)
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        queryset = ExternalContent.objects.all()
        authentication = MultiAuthentication(
            ApiKeyAuthentication(),
            UserAuthentication())
        authorization= Authorization()
        resource_name = 'external_content'
        excludes = ['username']

        filtering = {
            'id': ('exact',),
            'original_id': ('exact',),
            'store': ALL_WITH_RELATIONS
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
