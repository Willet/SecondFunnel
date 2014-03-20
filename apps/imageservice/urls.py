from django.conf.urls import patterns, url

# url prefix: /imagesevice/
# Essentially an API for interacting with the API

urlpatterns = patterns('apps.imageservice.views',
    # Default ImageService provided by our Django project
    # url(r'/create/?', 'create', name='create'),
    url(r'^store/(?P<store_id>\d+)/(?P<source>\w+)/create/?$', 'create_image', name='create_image'),
    url(r'^store/(?P<store_id>\d+)/product/(?P<product_id>\d+)/(?P<source>\w+)/create/?$', 'create_product_image', name='create_product_image'),

)
