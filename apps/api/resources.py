import django
from django.conf.urls import url
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from tastypie import http, fields
from tastypie.exceptions import Unauthorized, ImmediateHttpResponse
from tastypie.resources import ModelResource
from tastypie.utils import trailing_slash
from apps.api.utils import UserObjectsReadOnlyAuthorization
from apps.assets.models import Store


class StoreResource(ModelResource):
    class Meta:
        resource_name = 'internal_store'
        queryset = Store.objects.all()


# http://stackoverflow.com/questions/11770501/how-can-i-login-to-django-using-tastypie
class UserResource(ModelResource):
    stores = fields.ToManyField(
        StoreResource,
        'stores',  # Store::related_name(.staff)
        null=True,
        blank=True,
        full=True # There is a way to pick specific fields, but I don't recall.
    )

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
        csrf_token = django.middleware.csrf.get_token(request)

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