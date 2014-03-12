from django.conf.urls import patterns, url

urlpatterns = patterns('apps.intentrank.views',
    url(r'^page/(?P<page_id>\d+)/getresults/?$', 'get_results_view',
        name='get-results'),
    url(r'^tile/(?P<tile_id>\d+)/click/?$', 'click_tile',
        name='update-tile'),
    url(r'^tile/(?P<tile_id>\d+)/view/?$', 'view_tile',
        name='update-tile'),
    url(r'^page/(?P<page_id>\d+)/tile/(?P<tile_id>\d+)?$', 'get_tiles_view',
        name='get-tiles'),
    url(r'^page/(?P<page_id>\d+)/tile/?$', 'get_tiles_view',
        name='get-tiles'),
)
