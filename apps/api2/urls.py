from django.conf.urls import include, url
import views

urlpatterns = [
    url(r'^$', views.api_root, name='api-root'),

    url(r'^store/$', views.StoreList.as_view(), name='store-list'),
    url(r'^product/$', views.ProductList.as_view(), name='product-list'),
    url(r'^content/$', views.ContentList.as_view(), name='content-list'),
    url(r'^image/$', views.ImageList.as_view(), name='image-list'),
    url(r'^gif/$', views.GifList.as_view(), name='gif-list'),
    url(r'^productimage/$', views.ProductImageList.as_view(), name='productimage-list'),
    url(r'^video/$', views.VideoList.as_view(), name='video-list'),
    url(r'^page/$', views.PageList.as_view(), name='page-list'),
    url(r'^tile/$', views.TileList.as_view(), name='tile-list'),

    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
]
