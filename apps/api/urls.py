from django.conf.urls import url, patterns, include
from tastypie.api import Api

from apps.api.resources import UserResource
from apps.api.views import (ContentCGHandler, StoreContentCGHandler,
    StorePageContentCGHandler, ProductCGHandler, StoreProductCGHandler,
    StorePageProductCGHandler, StoreCGHandler, StoreItemCGHandler, PageCGHandler,
    StorePageCGHandler, TileConfigCGHandler, PageTileConfigCGHandler,
    StorePageItemCGHandler, StoreProductItemCGHandler, StorePageContentItemCGHandler,
    StoreContentItemCGHandler, TileConfigItemCGHandler,
    PageTileConfigItemCGHandler, StorePageTileConfigCGHandler,
    StorePageTileConfigItemCGHandler, CategoryCGHandler,
    StorePageContentSuggestedCGHandler, TileCGHandler, TileItemCGHandler,
    PageTileCGHandler, PageTileItemCGHandler, StorePageTileCGHandler,
    StorePageTileItemCGHandler, PageItemCGHandler, StorePageContentTagCGHandler,
    PageProductAllCGHandler, StorePageProductItemCGHandler,
    StorePageProductPrioritizeItemCGHandler,
    StorePageProductDeprioritizeItemCGHandler,
    StorePageContentPrioritizeItemCGHandler,
    StorePageContentDeprioritizeItemCGHandler, StoreContentApproveItemCGHandler,
    StoreContentRejectItemCGHandler, StoreContentUndecideItemCGHandler)
from apps.api.views.content import PageContentAllCGHandler
from apps.imageservice.views import create as imageservice_create

prefix = 'v1'

# tastypie routers
api = Api(api_name=prefix)
api.register(UserResource())

urlpatterns = api.urls

urlpatterns += patterns('apps.api.views',
    # primitive handlers
    # store
    url(r'^%s/store/?$' % prefix, StoreCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/?$' % prefix, StoreItemCGHandler.as_view()),

    url(r'^%s/category/?$' % prefix, CategoryCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/category/?$' % prefix, CategoryCGHandler.as_view()),

    # content
    url(r'^%s/content/?$' % prefix, ContentCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/content/?$' % prefix, StoreContentCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, StoreContentItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/?$' % prefix, StorePageContentCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, StorePageContentItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/tag/?$' % prefix, StorePageContentTagCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/tag/(?P<product_id>\d+)/?$' % prefix, StorePageContentTagCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/suggested/?$' % prefix, StorePageContentSuggestedCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/all/?$' % prefix, StoreContentCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/add_all/?$' % prefix, PageContentAllCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/?$' % prefix, StorePageContentItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/prioritize/?$' % prefix, StorePageContentPrioritizeItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/content/(?P<content_id>\d+)/deprioritize/?$' % prefix, StorePageContentDeprioritizeItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/approve/?$' % prefix, StoreContentApproveItemCGHandler.as_view()),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/reject/?$' % prefix, StoreContentRejectItemCGHandler.as_view()),
    url(r'%s/store/(?P<store_id>\d+)/content/(?P<content_id>\d+)/undecide/?$' % prefix, StoreContentUndecideItemCGHandler.as_view()),

    # product
    url(r'^%s/product/?$' % prefix, ProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/?$' % prefix, StoreProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_id>\d+)/?$' % prefix, StoreProductItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_set>\w+)/?$' % prefix, StoreProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_set>\w+)/(?P<product_id>\d+)/?$' % prefix, StoreProductItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/?$' % prefix, StorePageProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/all/?$' % prefix, StoreProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/add_all/?$' % prefix, PageProductAllCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/?$' % prefix, StorePageProductItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/prioritize/?$' % prefix, StorePageProductPrioritizeItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/deprioritize/?$' % prefix, StorePageProductDeprioritizeItemCGHandler.as_view()),

    # page
    url(r'^%s/page/?$' % prefix, PageCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/?$' % prefix, PageItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/?$' % prefix, StorePageCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/?$' % prefix, StorePageItemCGHandler.as_view()),

    # tileconfig
    url(r'^%s/tile-config/?$' % prefix, TileConfigCGHandler.as_view()),
    url(r'^%s/tile-config/(?P<tileconfig_id>\d+)/?$' % prefix, TileConfigItemCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/tile-config/?$' % prefix, PageTileConfigCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/tile-config/(?P<tileconfig_id>\d+)/?$' % prefix, PageTileConfigItemCGHandler.as_view()),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile-config/?$' % prefix, StorePageTileConfigCGHandler.as_view()),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile-config/(?P<tileconfig_id>\d+)/?$' % prefix, StorePageTileConfigItemCGHandler.as_view()),

    # tile
    url(r'^%s/tile/?$' % prefix, TileCGHandler.as_view()),
    url(r'^%s/tile/(?P<tile_id>\d+)/?$' % prefix, TileItemCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/tile/?$' % prefix, PageTileCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/tile/(?P<tile_id>\d+)/?$' % prefix, PageTileItemCGHandler.as_view()),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile/?$' % prefix, StorePageTileCGHandler.as_view()),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/tile/(?P<tile_id>\d+)/?$' % prefix, StorePageTileItemCGHandler.as_view()),

    # Intentrank Config
    url(r'^%s/store/(?P<store_id>\d+)/intentrank/(?P<ir_id>\d+)/?$' % prefix, 'generate_ir_config_view', name='generate_ir_config_view'),

    # Scraper
    url(r'^%s/scraper/store/(?P<store_id>\d+)/?$' % prefix, 'list_scrapers', name='list_scrapers'),

    # image service graph alias (needed for proxy)
    url(r'%s/imageservice/create/?$' % prefix, imageservice_create),

    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/generate/?$' % prefix, 'generate_static_page', name='generate_static_page'),
    url(r'%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/transfer/?$' % prefix, 'transfer_static_page', name='transfer_static_page'),

    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/(?P<object_type>\w+)/(?P<object_id>\d+)/?$' % prefix, 'proxy_tile', name='proxy_tile'),

    # If all else fails, proxy
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy_view', name='proxy_view'),
)
