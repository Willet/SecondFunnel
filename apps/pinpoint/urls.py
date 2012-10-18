from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('apps.pinpoint.views',
    url(r'admin/$', 'admin', name='admin'),

    url(r'admin/(?P<store_id>\d+)/$', 'store_admin', name='store-admin'),

    url(r'(?P<campaign_id>\d+)/$', 'campaign', name='campaign'),
)
