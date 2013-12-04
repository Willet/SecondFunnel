from django.conf.urls import *


urlpatterns = patterns('apps.mocks.views',
   url(r'^intentrank/getresults/?', 'get_results_view', name='get_results'),
   url(r'^intentrank/mock_tile/(?P<id>\d+)', 'tile_view', name = 'mock_tile'),
)
