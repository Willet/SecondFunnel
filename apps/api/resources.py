import django
from django.conf.urls import url
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from tastypie.http import HttpUnauthorized, HttpForbidden
from tastypie.resources import ModelResource
from tastypie.utils import trailing_slash


# http://stackoverflow.com/questions/11770501/how-can-i-login-to-django-using-tastypie
class UserResource(ModelResource):
    class Meta:
        resource_name = 'user'
        queryset = User.objects.all()
        excludes = ['id', 'email', 'password', 'is_staff', 'is_superuser']
        allowed_methods = ['get', 'post']
        # Do we need to allow querying / authorization?
        # Not right now, at least.

    def prepend_urls(self):
        """Adds URLs for login and logout"""
        login = url(
            r'^(?P<resource_name>%s)/login%s$' % (
                self._meta.resource_name, trailing_slash()),
            self.wrap_view('login'),
            name='api_login'
        )
        logout = url(
            r'^(?P<resource_name>%s)/logout%s$' % (
                self._meta.resource_name, trailing_slash()),
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
            return self.create_response(request, {
                'success': False,
                'reason': 'incorrect'
            }, HttpUnauthorized)

        if not user.is_active:
            return self.create_response(request, {
                'success': False,
                'reason': 'disabled'
            }, HttpForbidden)

        login(request, user)
        response = self.create_response(request, {
            'success': True
        })

        # Add CSRF token.
        csrf_token = django.middleware.csrf.get_token(request)
        response.set_cookie('csrftoken', csrf_token)

        return response

    def logout(self, request, **kwargs):
        self.method_check(request, allowed=['post'])

        if not request.user or not request.user.is_authenticated():
            return self.create_response(request, {
                'success': False
            }, HttpUnauthorized)

        logout(request)
        return self.create_response(request, {
            'success': True
        })
