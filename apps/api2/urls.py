from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
import views

router = DefaultRouter()
router.register(r'store', views.StoreViewSet)
router.register(r'product', views.ProductViewSet)
router.register(r'content', views.ContentViewSet)
router.register(r'image', views.ImageViewSet)
router.register(r'gif', views.GifViewSet)
router.register(r'productimage', views.ProductImageViewSet)
router.register(r'video', views.VideoViewSet)
router.register(r'page', views.PageViewSet)
router.register(r'tile', views.TileViewSet)
router.register(r'feed', views.FeedViewSet)
router.register(r'category', views.CategoryViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^store/$', views.StoreList.as_view(), name='store-list'),
    url(r'^product/$', views.ProductList.as_view(), name='product-list'),
    url(r'^content/$', views.ContentList.as_view(), name='content-list'),
    url(r'^image/$', views.ImageList.as_view(), name='image-list'),
    url(r'^gif/$', views.GifList.as_view(), name='gif-list'),
    url(r'^productimage/$', views.ProductImageList.as_view(), name='productimage-list'),
    url(r'^video/$', views.VideoList.as_view(), name='video-list'),
    url(r'^page/$', views.PageList.as_view(), name='page-list'),
    url(r'^tile/$', views.TileList.as_view(), name='tile-list'),
    url(r'^feed/$', views.FeedList.as_view(), name='feed-list'),
    url(r'^category/$', views.CategoryList.as_view(), name='category-list'),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
]
