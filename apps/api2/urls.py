from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
import views

# Create a router and register our viewsets with it.
router = DefaultRouter(trailing_slash=True)
router.register(r'^store', views.StoreViewSet)
router.register(r'^product', views.ProductViewSet)
router.register(r'^content', views.ContentViewSet)
router.register(r'^image', views.ImageViewSet)
router.register(r'^gif', views.GifViewSet)
router.register(r'^productimage', views.ProductImageViewSet)
router.register(r'^video', views.VideoViewSet)
router.register(r'^page', views.PageViewSet)
router.register(r'^tile', views.TileViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
]