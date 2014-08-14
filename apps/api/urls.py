from django.conf.urls import url, patterns, include
from tastypie.api import Api

from apps.api.resources import (
    UserResource, StoreResource, ProductResource, ProductImageResource, ReviewResource,
    VideoResource, ContentResource, ImageResource, ThemeResource, PageResource, FeedResource,
    TileResource, TileConfigResource, CampaignResource, CategoryResource)

from apps.api.views import (
    ContentCGHandler, StoreContentCGHandler,
    StorePageContentCGHandler, ProductCGHandler, StoreProductCGHandler,
    ProductImageItemCGHandler,
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
    StoreContentRejectItemCGHandler, StoreContentUndecideItemCGHandler, ProductItemCGHandler)

from apps.api.views.content import PageContentAllCGHandler

# tastypie v2 api
api = Api(api_name='v2')
api.register(UserResource())
api.register(StoreResource())
api.register(ProductResource())
api.register(ProductImageResource())
api.register(CategoryResource())
api.register(ContentResource())
api.register(ImageResource())
api.register(VideoResource())
api.register(ReviewResource())
api.register(ThemeResource())
api.register(FeedResource())
api.register(PageResource())
api.register(TileResource())
api.register(TileConfigResource())
api.register(CampaignResource())

urlpatterns = api.urls

# api urls v1
# This stuff can hopefully be removed when the CM is re-written..
prefix = 'v1'

urlpatterns += patterns(
    'apps.api.views',
    # primitive handlers
    # user
    url('%s/' % prefix, include(UserResource().urls)),  # v1 api uses UserResource from v2 for some reason..

    # store
    url(r'^%s/store/?$' % prefix, StoreCGHandler.as_view()),  # v2 mimics mostly
    url(r'^%s/store/(?P<store_id>\d+)/?$' % prefix, StoreItemCGHandler.as_view()),  # v2 mimics mostly

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
    url(r'^%s/product/(?P<product_id>\d+)/?$' % prefix, ProductItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/?$' % prefix, StoreProductCGHandler.as_view()),  # v2 mimics mostly
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_id>\d+)/?$' % prefix, StoreProductItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_set>\w+)/?$' % prefix, StoreProductCGHandler.as_view()),
    # what is product_set... product/live/# seems useless when you could just do product/#
    # everything is in the set live..
    url(r'^%s/store/(?P<store_id>\d+)/product/(?P<product_set>\w+)/(?P<product_id>\d+)/?$' % prefix, StoreProductItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/?$' % prefix, StorePageProductCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/all/?$' % prefix, PageProductAllCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/add_all/?$' % prefix, PageProductAllCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/?$' % prefix, StorePageProductItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/prioritize/?$' % prefix, StorePageProductPrioritizeItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/(?P<page_id>\d+)/product/(?P<product_id>\d+)/deprioritize/?$' % prefix, StorePageProductDeprioritizeItemCGHandler.as_view()),

    # product images
    url(r'^%s/productimage/(?P<id>\d+)/?$' % prefix, ProductImageItemCGHandler.as_view()),  # v2 mimics mostly

    # page
    url(r'^%s/page/?$' % prefix, PageCGHandler.as_view()),
    url(r'^%s/page/(?P<page_id>\d+)/?$' % prefix, PageItemCGHandler.as_view()),
    url(r'^%s/store/(?P<store_id>\d+)/page/?$' % prefix, StorePageCGHandler.as_view()),  # v2 mimics mostly
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

    # Scraper
    url(r'^%s/scraper/store/(?P<store_id>\d+)/?$' % prefix, 'list_scrapers', name='list_scrapers'),

    # image service graph alias (needed for proxy)
    url(r'%s/imageservice/' % prefix, include('apps.imageservice.urls')),

    # If all else fails, proxy
    url(r'^%s/(?P<path>.*)$' % prefix, 'proxy_view', name='proxy_view'),
)
