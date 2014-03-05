from django.conf.urls import patterns, url

# url prefix: /static_pages/

urlpatterns = patterns('apps.static_pages.views',
    # regenerate == generate
    url(r'^(?P<store_id>\d+)/(?P<page_id>\d+)/regenerate/?$',
        'generate_static_campaign', name='generate_static_campaign'),
)
