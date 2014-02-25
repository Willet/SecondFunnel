from django.conf.urls import *

from tastypie.api import Api

from apps.assets.api import (PageResource, ProductResource, StoreResource)

v1_api = Api(api_name='v1')
v1_api.register(PageResource())
v1_api.register(ProductResource())
v1_api.register(StoreResource())

urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
