from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('apps.pinpoint.views',
    url(r'^(?P<campaign_id_short>[A-Za-z0-9])/(?:(?P<mode>\w+).html)?$', 'campaign_short', name='campaign_short'),
)
