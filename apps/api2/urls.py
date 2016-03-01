from django.conf.urls import patterns, include, url
from rest_framework.routers import DefaultRouter
from rest_framework_bulk.routes import BulkRouter
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
router.register(r'feed', views.FeedViewSet)
router.register(r'category', views.CategoryViewSet)

router2 = BulkRouter()
router2.register(r'tile', views.TileViewSetBulk)

urlpatterns = patterns(
	'',
    url(r'^', include(router.urls)),
    url(r'^', include(router2.urls, namespace='rest_framework')),
)
