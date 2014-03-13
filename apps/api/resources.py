import calendar
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.http.response import Http404
import hammock
import json

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token

from tastypie import fields, http
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpMultipleChoices, HttpGone
from tastypie.resources import ModelResource, ALL
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash

from apps.api.paginator import ContentGraphPaginator
from apps.api.utils import UserObjectsReadOnlyAuthorization
from apps.assets.models import (Product, Store, Page, Feed, Tile, ProductImage, 
                                Image, Video, Review, Theme, TileRelation, Content)


ContentGraphClient = hammock.Hammock(settings.CONTENTGRAPH_BASE_URL, headers={'ApiKey': 'secretword'})


def to_cg_datetime(bundle_date):
    """Tastypie timbstamps look like "2014-03-10T11:32:32.805912"; convert
    that to a unix timestamp * 1000. You lose millisecond presicion.

    Part solution from http://stackoverflow.com/a/127872/1558430
    """
    return unicode(calendar.timegm(bundle_date.utctimetuple()) * 1000)


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

        authentication = UserAuthentication()

        filtering = {
            'id': ('exact',),
        }

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

        # changes the model's url (/store/123) to search by this field instead of the pk
        # http://stackoverflow.com/a/12517228/1558430
        detail_uri_name = 'old_id'

        authorization = UserPartOfStore()

        filtering = {
            'id': ('exact',),
            'name': ('icontains',),
            'slug': ALL,
        }

    def dehydrate(self, bundle):
        """Transform tastypie json to a CG-like version"""
        # http://django-tastypie.readthedocs.org/en/latest/cookbook.html#adding-custom-values
        bundle.data['public-base-url'] = bundle.data['public_base_url']
        del bundle.data['public_base_url']

        bundle.data['last-modified'] = to_cg_datetime(bundle.data['updated_at'])
        del bundle.data['updated_at']

        bundle.data['created'] = to_cg_datetime(bundle.data['created_at'])
        del bundle.data['created_at']

        # an unfortunate CM condition that requires the id to be the old id
        bundle.data['id'] = str(bundle.data['old_id'])

        return bundle

    def prepend_urls(self):
        """
        http://django-tastypie.readthedocs.org/en/latest/cookbook.html#nested-resources
        """
        return [
            url(r"^(?P<resource_name>%s)/(?P<old_id>\w[\w/-]*)/page/?$" % (self._meta.resource_name),
                self.wrap_view('get_pages'),
                name="api_get_pages"),
            url(r"^(?P<resource_name>%s)/(?P<old_id>\w[\w/-]*)/page/(?P<page_old_id>\w[\w/-]*)?$" % (self._meta.resource_name),
                self.wrap_view('get_page'),
                name="api_get_page"),
        ]

    def get_pages(self, request, **kwargs):
        try:
            bundle = self.build_bundle(data={'old_id': kwargs['old_id']}, request=request)
            obj = self.cached_obj_get(bundle=bundle,
                                      **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        sub_resource = PageResource()

        # just one:
        # return sub_resource.get_detail(request, store_id=obj.id)
        # more than one: http://stackoverflow.com/a/21763010/1558430
        return sub_resource.get_list(request, store_id=obj.id)

    def get_page(self, request, **kwargs):
        try:
            data = {'old_id': kwargs['old_id']}
            bundle = self.build_bundle(data=data, request=request)
            obj = self.cached_obj_get(bundle=bundle,
                                      **self.remove_api_resource_names(data))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        sub_resource = PageResource()

        # just one:
        return sub_resource.get_detail(request, old_id=kwargs['page_old_id'])
        # more than one: http://stackoverflow.com/a/21763010/1558430
        # return sub_resource.get_list(request, store_id=obj.id)

class ProductResource(BaseCGResource):
    """REST (tastypie) version of a Product."""
    store = fields.ForeignKey('apps.api.resources.StoreResource',
                              'store', full=False, null=True)

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


class ProductImageResource(BaseCGResource):
    """Returns "a product image"."""
    class Meta(BaseCGResource.Meta):
        queryset = ProductImage.objects.all()
        resource_name = 'product_image'

        filtering = {
            'store': ALL,
        }


class ContentResource(BaseCGResource):
    """Returns "a product image"."""
    class Meta(BaseCGResource.Meta):
        queryset = Content.objects.all()
        resource_name = 'content'

        # changes the model's url (/store/123) to search by this field instead of the pk
        # http://stackoverflow.com/a/12517228/1558430
        detail_uri_name = 'old_id'

        filtering = {
            'store': ALL,
        }

    def dehydrate(self, bundle):
        """Convert JSON fields into top-level attritbutes in the response"""
        # http://django-tastypie.readthedocs.org/en/latest/cookbook.html#adding-custom-values
        try:
            data = json.loads(json.dumps(bundle.obj.attributes))
            data.update(bundle.data)
            del data['attributes']
        except AttributeError:
            data = bundle.data

        bundle.data = data
        return bundle


class ImageResource(ContentResource):
    """Returns "a product image"."""
    class Meta(BaseCGResource.Meta):
        queryset = Image.objects.all()
        resource_name = 'image'

        filtering = {
            'store': ALL,
        }


class VideoResource(ContentResource):
    """Returns "a product image"."""
    class Meta(BaseCGResource.Meta):
        queryset = Video.objects.all()
        resource_name = 'video'

        filtering = {
            'store': ALL,
        }


class ReviewResource(ContentResource):
    """Returns "a product image"."""
    class Meta(BaseCGResource.Meta):
        queryset = Review.objects.all()
        resource_name = 'review'

        filtering = {
            'store': ALL,
        }


class ThemeResource(BaseCGResource):
    """Returns "a product image"."""
    class Meta(BaseCGResource.Meta):
        queryset = Theme.objects.all()
        resource_name = 'theme'

        filtering = {
            'store': ALL,
        }


class FeedResource(BaseCGResource):
    """Returns "a page"."""
    page = fields.RelatedField('apps.api.resources.PageResource',
                               'page', full=False, null=True)

    class Meta(BaseCGResource.Meta):
        queryset = Feed.objects.all()
        resource_name = 'feed'

        filtering = {
            'store': ALL,
        }


class PageResource(BaseCGResource):
    """Returns "a page"."""
    store = fields.ForeignKey('apps.api.resources.StoreResource',
                              'store', full=False, null=True)
    feed = fields.ForeignKey('apps.api.resources.FeedResource',
                             'feed', full=False, null=True)

    class Meta(BaseCGResource.Meta):
        queryset = Page.objects.all()
        resource_name = 'page'

        # changes the model's url (/store/123) to search by this field instead of the pk
        # http://stackoverflow.com/a/12517228/1558430
        detail_uri_name = 'old_id'

        filtering = {
            'store': ALL,
        }

    def dehydrate(self, bundle):
        """Convert JSON fields into top-level attritbutes in the response"""
        # http://django-tastypie.readthedocs.org/en/latest/cookbook.html#adding-custom-values
        try:
            data = json.loads(json.dumps(bundle.obj.theme_settings))
            data.update(bundle.data)
            del data['theme_settings']
        except AttributeError:
            data = bundle.data

        data['last-modified'] = to_cg_datetime(bundle.data['updated_at'])
        del data['updated_at']

        data['created'] = to_cg_datetime(data['created_at'])
        del data['created_at']

        # an unfortunate CM condition that requires the id to be the old id
        data['id'] = str(data['old_id'])

        bundle.data = data
        return bundle


class TileResource(BaseCGResource):
    """Returns "a page"."""
    feed = fields.ForeignKey('apps.api.resources.FeedResource',
                             'feed', full=False, null=True)

    class Meta(BaseCGResource.Meta):
        queryset = Tile.objects.all()
        resource_name = 'tile'

        # changes the model's url (/store/123) to search by this field instead of the pk
        # http://stackoverflow.com/a/12517228/1558430
        detail_uri_name = 'old_id'

        filtering = {
            'store': ALL,
        }


class TileRelationResource(BaseCGResource):
    """Returns "a page"."""
    class Meta(BaseCGResource.Meta):
        queryset = TileRelation.objects.all()
        resource_name = 'tile_relation'

        filtering = {
            'store': ALL,
        }


# http://stackoverflow.com/questions/11770501/how-can-i-login-to-django-using-tastypie
class UserResource(ModelResource):
    class Meta:
        resource_name = 'user'
        queryset = User.objects.all()
        excludes = ['id', 'email', 'password', 'is_staff', 'is_superuser']
        allowed_methods = ['get', 'post']
        authorization = UserObjectsReadOnlyAuthorization()

    def prepend_urls(self):
        """Adds URLs for login and logout"""
        login = url(
            r'^(?P<resource_name>%s)/login/?$' % (
                self._meta.resource_name),
            self.wrap_view('login'),
            name='api_login'
        )
        logout = url(
            r'^(?P<resource_name>%s)/logout/?$' % (
                self._meta.resource_name),
            self.wrap_view('logout'),
            name='api_logout'
        )

        return [login, logout]

    def login(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        data = self.deserialize(
            request,
            request.body
            # Format parameter never used... always application/json
        )

        username = data.get('username', '')
        password = data.get('password', '')

        user = authenticate(username=username, password=password)
        if not user:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        if not user.is_active:
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        # Add CSRF token. Nick is not a security expert
        csrf_token = get_token(request)

        login(request, user)

        return self.get_detail(request, username=username)

    def logout(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        if not request.user or not request.user.is_authenticated():
            raise ImmediateHttpResponse(response=http.HttpUnauthorized())

        logout(request)
        return self.create_response(request, {
            'success': True
        })
