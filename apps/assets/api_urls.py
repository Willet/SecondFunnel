from django.conf.urls.defaults import *

from tastypie.api import Api

from apps.assets.api import BlockContentResource, CampaignResource,\
    ExternalContentResource, ProductResource, ProductMediaResource, \
    StoreResource

v1_api = Api(api_name='v1')
v1_api.register(BlockContentResource())
v1_api.register(CampaignResource())
v1_api.register(ExternalContentResource())
v1_api.register(ProductMediaResource())
v1_api.register(ProductResource())
v1_api.register(StoreResource())


urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
