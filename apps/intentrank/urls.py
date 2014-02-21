from django.conf.urls import patterns, url

urlpatterns = patterns('apps.intentrank.views',
    url(r'^update-clickstream/$', 'update_clickstream',
        name='update-clickstream'),

   url(r'^page/(?P<page>\d+)/getresults$', 'get_results', name='get-results'),
   url(r'^(?P<url>.+)$', 'get_results', name='get-results'),
)
