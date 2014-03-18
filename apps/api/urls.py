from django.conf.urls import url, patterns, include
from tastypie.api import Api

from apps.api.resources import UserResource
from apps.api.views import (ContentCGHandler, StoreContentsCGHandler,
    StorePageContentCGHandler, ProductCGHandler, StoreProductsCGHandler,
    StorePageProductCGHandler, StoreCGHandler, PageCGHandler,
    StorePageCGHandler, TileConfigCGHandler, PageTileConfigCGHandler,
    StorePagesCGHandler, StoreProductCGHandler, StorePageContentsCGHandler,
    StoreContentCGHandler)

prefix = 'v1'

# tastypie routers
api = Api(api_name=prefix)
api.register(UserResource())

urlpatterns = api.urls

urlpatterns += patterns('apps.api.views',
    # primitive handlers
    # store
    url(r'^%s/store/?$' % prefix, StoreCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/?$' % prefix, StoreCGHandler.as_view()),

    # content
    url(r'^%s/content/?$' % prefix, ContentCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/content/?$' % prefix, StoreContentsCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, StoreContentCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/?$' % prefix, StorePageContentsCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, StorePageContentCGHandler.as_view()),

    # product
    url(r'^%s/product/?$' % prefix, ProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/?$' % prefix, StoreProductsCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_set>\w+)/?$' % prefix, StoreProductsCGHandler.as_view()),  # TODO: actually filter by sets (live, all, ...)
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_set>\w+)/(?P<product_id>\d+)/?$' % prefix, StoreProductCGHandler.as_view()),  # TODO: actually filter by sets (live, all, ...)
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/?$' % prefix, StorePageProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/all/?$' % prefix, StorePageProductCGHandler.as_view()),

    # page
    url(r'^%s/page/(?P<page_id>\d+)/?$' % prefix, PageCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/?$' % prefix, StorePagesCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/?$' % prefix, StorePageCGHandler.as_view()),

    # tileconfig
    url(r'^%s/tile-config/?$' % prefix, TileConfigCGHandler.as_view()),
    url(r'^%s/tile-config/(?P<tileconfig_id>\d+)/?$' % prefix, TileConfigCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/tile-config/?$' % prefix, PageTileConfigCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/tile-config/(?P<tileconfig_id>\d+)/?$' % prefix, PageTileConfigCGHandler.as_view()),

    url(r'^%s/store/(?P<store_id>\d+)'
        r'/page/(?P<page_id>\d+)'
        r'/content/suggested/?$' % prefix,
        'get_suggested_content_by_page',
        name='get_suggested_content_by_page'),

    url(r'^%s/store/(?P<store_id>\d+)'
        r'/page/(?P<page_id>\d+)'
        r'/content/(?P<content_id>\d+)'
        r'/tag/?$' % prefix,
        'tag_content',
        name='tag_content'),

    url(r'^%s/store/(?P<store_id>\d+)'
        r'/page/(?P<page_id>\d+)'
        r'/content/(?P<content_id>\d+)'
        r'/tag'
        r'/(?P<product_id>\d+)/?$' % prefix,
        'tag_content',
        name='delete_tagged_content'),

    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/add_all/?$' % prefix, 'add_all_products', name='add_all_products'),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/add_all/?$' % prefix, 'add_all_content'),

    url(r'^%s/check_queue/(?P<queue_name>[^\/]*)/?$' % prefix,
        'check_queue',
        name='check_queue'),

    # url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, 'content_operations', name='content_operations'),
    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/approve/?$' % prefix, 'approve_content', name='approve_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/reject/?$' % prefix, 'reject_content', name='reject_content'),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/undecide/?$' % prefix, 'undecide_content', name='undecide_content'),

    # Intentrank Config
    url(r'^%s/store/(?P<store_id>\d+)/intentrank/(?P<ir_id>\d+)/?$' % prefix, 'generate_ir_config_view', name='generate_ir_config_view'),

    # Scraper
    url(r'^%s/scraper/store/(?P<store_id>\d+)/?$' % prefix, 'list_scrapers', name='list_scrapers'),
    url(r'^%s/scraper/store/(?P<store_id>\d+)/(?P<scraper_name>.*?)/?$' % prefix, 'delete_scraper', name='delete_scraper'),

    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, 'page_content_operations', name='page_content_operations'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/prioritize/?$' % prefix, 'prioritize_content', name='prioritize_content'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/deprioritize/?$' % prefix, 'deprioritize_content', name='deprioritize_content'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/all/?$' % prefix, 'list_page_all_content', name='list_page_all_content'),

    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/?$' % prefix, 'product_operations', name='product_operations'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/prioritize/?$' % prefix, 'prioritize_product', name='prioritize_product'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/deprioritize/?$' % prefix, 'deprioritize_product', name='deprioritize_product'),
    #url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/all/?$' % prefix, 'list_page_all_products', name='list_page_all_products'),

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
