from django.conf.urls import patterns, url

urlpatterns = patterns('apps.intentrank.views',
    url(r'^get-seeds/$', 'get_seeds', name='get-seeds'),

    url(r'^update-clickstream/$', 'update_clickstream',
        name='update-clickstream'),

   url(r'^(?P<url>.+)$',
       'get_results', name='get-results'),
)
