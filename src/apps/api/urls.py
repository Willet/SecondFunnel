from django.conf.urls import *
from tastypie.api import Api
from apps.api.resources import UserResource

prefix = 'v1'

api = Api(api_name=prefix)
api.register(UserResource())

urlpatterns = api.urls

# TODO: non-api URLS don't belong here

# Sink function; if all else fails, proxy
urlpatterns += patterns('apps.contentgraph.views',
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy', name='proxy')
)