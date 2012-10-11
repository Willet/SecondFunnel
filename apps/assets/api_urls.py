from django.conf.urls.defaults import *

from tastypie.api import Api

from apps.assets.api import ProductResource, ProductMediaResource, StoreResource

v1_api = Api(api_name='v1')
v1_api.register(ProductResource())
v1_api.register(StoreResource())
v1_api.register(ProductMediaResource())


urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
