from django.conf.urls import *
from tastypie.api import Api
from apps.api.resources import UserResource

prefix = 'v1'

api = Api(api_name=prefix)
api.register(UserResource())

urlpatterns = api.urls

urlpatterns += patterns('apps.api.views',
    url(r'^%s/store/(?P<store_id>[^\/]*)/page/(?P<page_id>[^\/]*)/content/by-id?$' % prefix,
        'get_page_content_by_product',
        name='get_page_content_by_product'),
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy_view', name='proxy_view'),
)
