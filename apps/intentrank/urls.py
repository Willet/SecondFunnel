from django.conf.urls import patterns, url

urlpatterns = patterns('apps.intentrank.views',
    url(r'^page/(?P<page>\d+)/getresults$', 'get_results_view',
        name='get-results'),
    url(r'^(?P<url>.+)$', 'get_results_view',
        name='get-results'),
)
