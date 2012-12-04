from django.conf.urls.defaults import patterns, url

# TODO: Replace with TastyPie
urlpatterns = patterns('apps.intentrank.views',
   url(r'^get-seeds/$', 'get_seeds', name='get-seeds'),
   url(r'^get-results/$', 'get_results', name='get-results'),
   url(r'^update-clickstream/$', 'update_clickstream',
       name='update-clickstream'),
)