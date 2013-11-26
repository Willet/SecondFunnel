from django.conf.urls import *
from tastypie.api import Api
from apps.api.resources import UserResource

prefix = 'v1'

api = Api(api_name=prefix)
api.register(UserResource())

urlpatterns = api.urls

urlpatterns += patterns('apps.api.views',
    url(
        r'^%s/store/(?P<store_id>\d+)'
        r'/page/(?P<page_id>\d+)'
        r'/content/(?P<content_id>\d+)/?$' % prefix,
        'proxy_content',
        name='proxy_content'
    ),
    url(r'^%s/store/(?P<store_id>[^\/]*)'
        r'/page/(?P<page_id>[^\/]*)'
        r'/content/suggested/?$' % prefix,
        'get_suggested_content_by_page',
        name='get_suggested_content_by_page'),
    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/approve/?$' % prefix, 'approve_content', name='approve_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/reject' % prefix, 'reject_content', name='reject_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/undecide' % prefix, 'undecide_content', name='undecide_content'),
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy_view', name='proxy_view'),
)
