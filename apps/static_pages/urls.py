from django.conf.urls import patterns, url

# url prefix: /static_pages/

urlpatterns = patterns('apps.static_pages.views',
    url(r'^(?P<store_id>\d+)/(?P<campaign_id>\d+)/regenerate/?$',
        'regenerate_static_campaign', name='regenerate_static_campaign'),
)
