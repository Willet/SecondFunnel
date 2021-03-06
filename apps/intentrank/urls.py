from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.intentrank.views',

    url(r'^/?$', 'get_overview'),
    url(r'^page/(?P<page_id>\d+)/getresults/?$', 'get_results_view',
        name='get-results'),
    url(r'^page/(?P<page_id>\d+)/tile/(?P<tile_id>\d+)/?$', 'get_tiles_view'),
    url(r'^page/(?P<page_id>\d+)/tile/(?P<action>[a-z]+)/?$', 'track_tiles'),
    url(r'^page/(?P<page_id>\d+)/tile/?$', 'get_tiles_view'),
)
