from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from apps.assets.models import (Product, Store, ProductMedia, ExternalContent,
    YoutubeVideo, GenericImage, ExternalContent, ExternalContentType)

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

        filtering = {
            'store': ALL,
        }


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
        authentication = UserAuthentication()
        authorization= Authorization()
        resource_name = 'external_content'

        filtering = {
            'id': ('exact',),
            'original_id': ('exact',),
            'store': ALL_WITH_RELATIONS
        }

    def dehydrate_type(self, bundle):
        return bundle.data['type'].data['slug']