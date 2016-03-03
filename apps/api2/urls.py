from django.conf.urls import patterns, include, url
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
router.register(r'feed', views.FeedViewSet)
router.register(r'category', views.CategoryViewSet)

urlpatterns = patterns(
	'',
    url(r'^', include(router.urls)),
    url(r'^tile$', views.TileViewSetBulk.as_view()),
    url(r'^tile/(?P<pk>[0-9]+)/$', views.TileDetailBulk.as_view()),
)
