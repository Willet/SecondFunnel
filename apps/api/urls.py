from django.conf.urls import *
from django.http import HttpResponse
from tastypie.api import Api
from apps.api.resources import UserResource

prefix = 'v1'

api = Api(api_name=prefix)
api.register(UserResource())

urlpatterns = api.urls

urlpatterns += patterns('apps.api.views',
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy_view', name='proxy_view')
)