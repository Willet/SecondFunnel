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
from tastypie.serializers import Serializer
from apps.api.paginator import ContentGraphPaginator

from apps.assets.models import (Product, Store, Page, Feed, Tile)


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


class BaseCGResource(ModelResource):
    """Alters the 'objects' and 'meta' keys given by the default paginator."""
    class Meta:
        serializer = Serializer(formats=['json'])
        paginator_class = ContentGraphPaginator

    def alter_list_data_to_serialize(self, request, data):
        data['results'] = data['objects']
        del data['objects']
        return data

    def alter_deserialized_list_data(self, request, data):
        data['objects'] = data['results']
        del data['results']
        return data


class StoreResource(BaseCGResource):
    """REST-style store."""
    class Meta(BaseCGResource.Meta):
        queryset = Store.objects.all()
        resource_name = 'store'

        authentication = UserAuthentication()
        authorization = UserPartOfStore()
        filtering = {
            'id': ('exact',),
            'name': ('icontains',),
        }


class ProductResource(BaseCGResource):
    """REST (tastypie) version of a Product."""
    store = fields.ForeignKey(StoreResource, 'store')

    class Meta(BaseCGResource.Meta):
        """Django's way of defining a model's metadata."""
        queryset = Product.objects.all()
        resource_name = 'product'

        filtering = {
            'store': ALL,
            'id': ('exact',),
            'name': ('exact', 'contains',),
            # 'name_or_url': ('exact'),
            # 'available': ('exact'),
        }
        authentication = UserAuthentication()
        authorization = UserPartOfStore()


class PageResource(BaseCGResource):
    """Returns "a page"."""
    store = fields.ForeignKey(StoreResource, 'store', full=True)

    class Meta(BaseCGResource.Meta):
        queryset = Page.objects.all()
        resource_name = 'page'

        filtering = {
            'store': ALL,
        }


class FeedResource(BaseCGResource):
    """Returns "a page"."""
    page = fields.ForeignKey(PageResource, 'feed', full=False)

    class Meta(BaseCGResource.Meta):
        queryset = Feed.objects.all()
        resource_name = 'feed'

        filtering = {
            'store': ALL,
        }


class TileResource(BaseCGResource):
    """Returns "a page"."""
    feed = fields.ForeignKey(FeedResource, 'feed', full=False)

    class Meta(BaseCGResource.Meta):
        queryset = Tile.objects.all()
        resource_name = 'tile'

        filtering = {
            'store': ALL,
        }
