from django.conf.urls import *
from tastypie.api import Api
from apps.api.resources import UserResource

prefix = 'v1'

api = Api(api_name=prefix)
api.register(UserResource())

urlpatterns = api.urls

urlpatterns += patterns('apps.api.views',
    url(
        r'^%s/store/(?P<store_id>\d+)'          # store
        r'/page/(?P<page_id>\d+)'               # page
        r'/(?P<object_type>\w+)'                # type
        r'/(?P<object_id>\d+)/?$' % prefix,     # id
        'proxy_tile',
        name='proxy_tile'
    ),
    url(r'^%s/store/(?P<store_id>[^\/]*)'
        r'/page/(?P<page_id>[^\/]*)'
        r'/content/suggested/?$' % prefix,
        'get_suggested_content_by_page',
        name='get_suggested_content_by_page'),

    url(r'^%s/store/(?P<store_id>[^\/]*)'
        r'/page/(?P<page_id>[^\/]*)'
        r'/content/(?P<content_id>[^\/]*)'
        r'/tag/?$' % prefix,
        'tag_content',
        name='tag_content'),

    url(r'^%s/store/(?P<store_id>[^\/]*)'
        r'/page/(?P<page_id>[^\/]*)'
        r'/content/(?P<content_id>[^\/]*)'
        r'/tag'
        r'/(?P<product_id>[^\/]*)/?$' % prefix,
        'tag_content',
        name='delete_tagged_content'),

    url(r'^%s/store/(?P<store_id>\d+)'
        r'/page/(?P<page_id>\d+)'
        r'/content/add_all/?$' % prefix,
        'add_all_content', name='add_all_content'),

    url(r'^%s/check_queue/(?P<queue_name>[^\/]*)/?$' % prefix,
        'check_queue',
        name='check_queue'),

    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/approve/?$' % prefix, 'approve_content', name='approve_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/reject/?$' % prefix, 'reject_content', name='reject_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/undecide/?$' % prefix, 'undecide_content', name='undecide_content'),

    # Scraper
    url(r'^%s/scraper/store/(?P<store_id>\d+)/?$' % prefix, 'list_scrapers', name='list_scrapers'),
    url(r'^%s/scraper/store/(?P<store_id>\d+)/(?P<scraper_name>.*?)/?$' % prefix, 'delete_scraper', name='delete_scraper'),

    # If all else fails, proxy
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy_view', name='proxy_view'),
)
