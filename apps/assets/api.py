from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf.urls import url
from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.models import ApiKey
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import Authentication, ApiKeyAuthentication, MultiAuthentication
from tastypie.authorization import Authorization, ReadOnlyAuthorization
from django.db.models import Q

from apps.assets.models import (Product, Store, ProductMedia, ExternalContent,
    YoutubeVideo, GenericImage, ExternalContent, ExternalContentType)

from apps.assets.api_utils import PrettyJSONSerializer
from apps.pinpoint.models import BlockContent, Campaign


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
        custom_filters = []

        cust

    # Attempt 2
    # TODO: Is there a better way to do this?
    def build_filters(self, filters=None):
        """Builds a list of filters using the custom filters and the ModelResource
        filters as defined by the Meta.filtering.

        @param filters: QueryDict of filters to use.
        @return: dict
        """
        filters = filters or {}
        custom_filters = self.Meta.custom_filters
        non_custom_filters = {}

        # Exclusionary check to prevent type errors in case custom filters are more
        # advanced.
        for _filter in filters:
            if not _filter in custom_filters:
                non_custom_filters[_filter] = filters[_filter]

        orm_filters = super(FilteredModelResource, self).build_filters(non_custom_filters)

        queries = filters.dict()
        for _filter in filters:
            # Look for functions defined as [filter_name]_filter
            try:
                get_filter = getattr(self, "%s_filter"%_filter)
                orm_filters.update(get_filter(**queries))
            except AttributeError:
                continue

        return orm_filters

    def apply_filters(self, request, applicable_filters):
        """Apply the filters by seperating the custom ones from the non-custom ones; custom
        ones are applied seperately (expected to be Q objects).

        @param request: The user request object
        @param applicable_filters: A dict of filters to be applied.
        @return: object or list of objects
        """
        custom_filters = self.Meta.custom_filters
        custom = []

        for _filter in custom_filters:
            if _filter in applicable_filters:
                custom.append(applicable_filters.pop(_filter))

        semi_filtered = super(FilteredModelResource, self).apply_filters(request, applicable_filters)

        for _filter in custom:
            semi_filtered = semi_filtered.filter(_filter)

        return semi_filtered


class WriteAuthorization(ReadOnlyAuthorization, UserPartOfStore):
    """ Read-only resource.  When user is authorized, then they have access to
    PUT/POST/DELETE"""
    def is_authorized(self, request, object=None):
        return super(WriteAuthorization, self).is_authorized(request, object)

    def create_detail(self, object_list, bundle):
        return self.is_authorized(bundle.request, object_list)

    def update_list(self, object_list, bundle):
        return object_list if self.is_authorized(bundle.request, object_list) else []

    def update_detail(self, object_list, bundle):
        return self.is_authorized(bundle.request, object_list)

    def delete_list(self, object_list, bundle):
        return object_list if self.is_authorized(bundle.request, object_list) else []

    def delete_detail(self, object_list, bundle):
        return self.is_authorized(bundle.request, object_list)


class BlockContentResource(ModelResource):
    """Returns a campaign's content blocks."""
    class Meta:
        queryset = BlockContent.objects.all()
        resource_name = 'block_content'
        serializer = PrettyJSONSerializer()

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
        serializer = PrettyJSONSerializer()
        filtering = {
            'id': ('exact',),
            'name': ('icontains',),
        }


class ProductResource(FilteredModelResource):
    """REST (tastypie) version of a Product."""
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta:
        """Django's way of defining a model's metadata."""
        queryset = Product.objects.all()
        resource_name = 'product'
        serializer = PrettyJSONSerializer()
        custom_filters = ['name_or_url', 'available']

        filtering = {
            'store': ALL,
            'id': ('exact',),
            'name': ('exact', 'contains',),
            'name_or_url': ('exact'),
            'available': ('exact'),
        }
        authentication = UserAuthentication()
        authorization = UserPartOfStore()


    def name_or_url_filter(self, name_or_url, **kwargs):
        return (
            Q(name__icontains=name_or_url) |
            Q(original_url__startswith=name_or_url)
        )

    def build_filters(self, filters=None):
        """build_filters (transitions) resource lookup to an ORM lookup.

        Also an extended defined function from ModelResource in tastypie.
        """
        orm_filters = super(ProductResource, self).build_filters(filters)

        availability = filters.get('available', True)
        if availability:
            qset = (Q(available=availability))
            orm_filters.update({'available': qset})

        return orm_filters


class ProductMediaResource(ModelResource):
    product = fields.ForeignKey(ProductResource, 'product')

    class Meta:
        queryset = ProductMedia.objects.all()
        resource_name = 'product_media'
        serializer = PrettyJSONSerializer()

        filtering = {
            'product': ALL
        }
        authentication = UserAuthentication()
        authorization = UserPartOfStore()


class CampaignResource(ModelResource):
    """Returns "a campaign".

    Campaign definitions are saved in apps/pinpoint/models.py.
    """
    store = fields.ForeignKey(StoreResource, 'store', full=True)
    content_blocks = fields.ToManyField(BlockContentResource, 'content_blocks',
                                        full=True)
    discovery_blocks = fields.ToManyField(BlockContentResource,
                                          'discovery_blocks', full=True)

    class Meta:
        queryset = Campaign.objects.all()
        resource_name = 'campaign'
        serializer = PrettyJSONSerializer()

        filtering = {
            'store': ALL,
        }


class YoutubeVideoResource(ModelResource):
    """Access to youtube video model"""

    class Meta:
        queryset = YoutubeVideo.objects.all()
        authentication = UserAuthentication()
        resource_name = 'youtube_video'
        serializer = PrettyJSONSerializer()

        filtering = {
            'id': ('exact',)
        }


class GenericImageResource(ModelResource):
    """Access to GenericImage model"""

    class Meta:
        queryset = GenericImage.objects.all()
        authentication = UserAuthentication()
        resource_name = 'generic_image'
        serializer = PrettyJSONSerializer()

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
        serializer = PrettyJSONSerializer()


class ExternalContentResource(FilteredModelResource):
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
        serializer = PrettyJSONSerializer()
        excludes = ['created']
        ordering = ['last_modified', 'created']
        custom_filters = ['type', 'store', 'tags', 'text', 'original_url']

        custom_filtering = {
            'type': ('content_type__name__iexact'),

        }

        filtering = {
            'id': ('exact',),
            'original_id': ('exact',),
            'store': ALL_WITH_RELATIONS,
            'active': ('exact',),
            'approved': ('exact',),
            'type': ('exact',),
            'tags': ('exact',),
            'text': ('exact',),
            'original_url': ('exact', 'contains'),
            'date': ('exact',),
        }

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<store>(?!\d+/$)[\w\d_.:\-\s]+)/$"% self._meta.resource_name,
                self.wrap_view('dispatch_list'), name="api_dispatch_list"),
        ]

    def type_filter(self, type, **kwargs):
        # so wrong
        try:
            int(type)
        except ValueError:
            return {'type': Q(content_type__name__iexact=type)}
        return {}

    def store_filter(self, store, **kwargs):
        try:
            int(store)
        except ValueError:
            return {'store': Q(store__name__iexact=store)}
        return {}

    def text_filter(self, text, **kwargs):
        return {'text': Q(text_content__contains=text)}

    def original_url_filter(self, original_url, **kwargs):
        return {'original_url': Q(original_url__contains=original_url)}

    def tags_filter(self, tags, **kwargs):
        tags = tags.split(",")
        try:
            int(tags[0])
            return {'tags': Q(tagged_products__id__in=tags)}
        except ValueError:
            pass
        return {'tags': Q(tagged_products__name__in=tags)}


# Apparently, create_api_key only creates on user creation
# Resolve this by creating a key if the key doesn't exist.
def get_or_create_api_key(sender, **kwargs):
    user = kwargs.get('instance')

    if not user:
        return

    ApiKey.objects.get_or_create(user=user)


# signals
post_save.connect(get_or_create_api_key, sender=User)
