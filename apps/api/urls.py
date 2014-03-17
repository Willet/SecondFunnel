from django.conf.urls import url, patterns, include
from tastypie.api import Api
from rest_framework_nested import routers

from apps.api.resources import (ProductResource, StoreResource, PageResource,
                                TileResource, FeedResource, UserResource,
                                ProductImageResource, ImageResource, VideoResource,
                                ThemeResource, ReviewResource, TileRelationResource,
                                ContentResource, StoreViewSet, PageViewSet, FeedViewSet, TileConfigResource)

prefix = 'v1'

# tastypie routers
api = Api(api_name=prefix)
api.register(UserResource())
# api.register(StoreResource())
# api.register(ProductResource())
api.register(ProductImageResource())
# api.register(ContentResource())
api.register(ImageResource())
api.register(VideoResource())
api.register(ReviewResource())
api.register(ThemeResource())
api.register(PageResource())
api.register(FeedResource())
api.register(TileResource())
api.register(TileConfigResource())
api.register(TileRelationResource())

urlpatterns = api.urls

urlpatterns += patterns('apps.api.views',
    # primitive handlers
    url(r'^%s/product/?$' % prefix, 'product'),
    url(r'^%s/product/(?P<product_id>[^\/]*)/?$' % prefix, 'product'),
    url(r'^%s/content/?$' % prefix, 'content'),
    url(r'^%s/content/(?P<content_id>[^\/]*)/?$' % prefix, 'content'),
    url(r'^%s/store/(?P<store_id>[^\/]*)/content/?$' % prefix, 'store_content'),
    url(r'^%s/store/(?P<store_id>[^\/]*)/content/(?P<content_id>[^\/]*)/?$' % prefix, 'store_content'),

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
        r'/product/add_all/?$' % prefix,
        'add_all_products', name='add_all_products'),

    url(r'^%s/store/(?P<store_id>\d+)'
        r'/page/(?P<page_id>\d+)'
        r'/content/add_all/?$' % prefix,
        'add_all_content', name='add_all_content'),

    url(r'^%s/check_queue/(?P<queue_name>[^\/]*)/?$' % prefix,
        'check_queue',
        name='check_queue'),

    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, 'content_operations', name='content_operations'),
    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/approve/?$' % prefix, 'approve_content', name='approve_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/reject/?$' % prefix, 'reject_content', name='reject_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/undecide/?$' % prefix, 'undecide_content', name='undecide_content'),

    # Intentrank Config
    url(r'^%s/store/(?P<store_id>\d+)/intentrank/(?P<ir_id>\d+)/?$' % prefix, 'generate_ir_config_view', name='generate_ir_config_view'),

    # Scraper
    url(r'^%s/scraper/store/(?P<store_id>\d+)/?$' % prefix, 'list_scrapers', name='list_scrapers'),
    url(r'^%s/scraper/store/(?P<store_id>\d+)/(?P<scraper_name>.*?)/?$' % prefix, 'delete_scraper', name='delete_scraper'),

    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/?$' % prefix, 'modify_page', name='modify_page'),

    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/?$' % prefix, 'list_page_content', name='list_page_content'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, 'page_content_operations', name='page_content_operations'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/prioritize/?$' % prefix, 'prioritize_content', name='prioritize_content'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/deprioritize/?$' % prefix, 'deprioritize_content', name='deprioritize_content'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/all/?$' % prefix, 'list_page_all_content', name='list_page_all_content'),

    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/?$' % prefix, 'list_page_products', name='list_page_products'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/?$' % prefix, 'product_operations', name='product_operations'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/prioritize/?$' % prefix, 'prioritize_product', name='prioritize_product'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/deprioritize/?$' % prefix, 'deprioritize_product', name='deprioritize_product'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/all/?$' % prefix, 'list_page_all_products', name='list_page_all_products'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile-config/?$' % prefix, 'list_page_tile_configs', name='list_page_tile_configs'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile-config/(?P<tileconfig_id>\d+)/?$' % prefix, 'get_page_tile_config', name='get_page_tile_config'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile-config/(?P<tileconfig_id>\d+)/prioritize/?$' % prefix, 'prioritize_tile', name='prioritize_tile'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile-config/(?P<tileconfig_id>\d+)/deprioritize/?$' % prefix, 'deprioritize_tile', name='deprioritize_tile'),

    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/generate/?$' % prefix, 'generate_static_page', name='generate_static_page'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/transfer/?$' % prefix, 'transfer_static_page', name='transfer_static_page'),

    url(
        r'^%s/store/(?P<store_id>\d+)'          # store
        r'/page/(?P<page_id>\d+)'               # page
        r'/(?P<object_type>\w+)'                # type
        r'/(?P<object_id>\d+)/?$' % prefix,     # id
        'proxy_tile',
        name='proxy_tile'
    ),

    # If all else fails, proxy
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy_view', name='proxy_view'),
)
