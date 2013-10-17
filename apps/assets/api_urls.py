from django.conf.urls import *

from tastypie.api import Api

from apps.assets.api import (CampaignResource,
    ProductResource, StoreResource, StoreThemeResource,
    YoutubeVideoResource)

v1_api = Api(api_name='v1')
v1_api.register(CampaignResource())
v1_api.register(ProductResource())
v1_api.register(StoreResource())
v1_api.register(StoreThemeResource())
v1_api.register(YoutubeVideoResource())

urlpatterns = patterns('',
    (r'', include(v1_api.urls)),
)
