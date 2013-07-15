from django.conf.urls import patterns, url

# TODO: Replace with TastyPie
urlpatterns = patterns('apps.intentrank.views',
   url(r'^get-results/$', 'get_results', name='get-results'),

   # TEMPORARY: These methods should be removed as soon as Neal's
   # service is fully operational
   url(r'^get-related-content/product/(?P<id>\w+)$', 'get_related_content_product',
       name='get-related-content-product'),
   url(r'^get-related-content/store/(?P<id>\w+)$', 'get_related_content_store',
       name='get-related-content-store'),
)
