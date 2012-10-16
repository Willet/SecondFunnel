from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('apps.pinpoint.views',
    url(r'(?P<campaign_id>\d+)/admin/$', 'pinpoint_admin'),
    url(r'(?P<campaign_id>\d+)/$', 'campaign',
        name='campaign'),
)
