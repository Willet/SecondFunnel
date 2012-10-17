from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('apps.pinpoint.views',
    # url(r'(?P<store_id>\d+)/admin$', 'store_admin', name="store-admin"),
    url(r'(?P<campaign_id>\d+)/$', 'campaign',
        name='campaign'),
)
