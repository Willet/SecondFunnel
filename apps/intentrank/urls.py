from django.conf.urls import patterns, url

# TODO: Replace with TastyPie
urlpatterns = patterns('apps.intentrank.views',
    url(r'^get-seeds/$', 'get_seeds', name='get-seeds'),

    url(r'^get-results/$', 'get_results', name='get-results'),
    url(r'^update-clickstream/$', 'update_clickstream',
        name='update-clickstream'),
    url(r'^invalidate-session/$', 'invalidate_session',
        name='invalidate_session'),

   # New IR functions: Dev only
   url(r'^store/(?P<store_slug>[a-zA-Z0-9 -_]+)/campaign/(?P<campaign>\d+)/getresults$',
       'get_results_dev', name='get-results'),

   url(r'^store/(?P<store_slug>\w+)/campaign/(?P<campaign>\d+)/content/'
       r'(?P<content_id>\w+)/getresults$', 'get_results_dev', name='get-results'),

   # TEMPORARY: These methods should be removed as soon as Neal's
   # service is fully operational
   url(r'^get-related-content/product/(?P<id>\w+)$', 'get_related_content_product',
       name='get-related-content-product'),
   url(r'^get-related-content/store/(?P<id>\w+)$', 'get_related_content_store',
       name='get-related-content-store'),
)
