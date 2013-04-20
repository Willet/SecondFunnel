from django.conf.urls.defaults import *

from tastypie.api import Api

from apps.assets.api import (BlockContentResource, CampaignResource,
    ProductResource, ProductMediaResource, StoreResource,
    YoutubeVideoResource, GenericImageResource, ExternalContentResource)

v1_api = Api(api_name='v1')
v1_api.register(BlockContentResource())
v1_api.register(CampaignResource())
v1_api.register(ProductMediaResource())
v1_api.register(ProductResource())
v1_api.register(StoreResource())
v1_api.register(YoutubeVideoResource())
v1_api.register(GenericImageResource())
v1_api.register(ExternalContentResource())


urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
