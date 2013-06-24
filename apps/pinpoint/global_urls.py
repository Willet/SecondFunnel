from django.conf.urls import patterns, url

urlpatterns = patterns('apps.pinpoint.views',
   # As suggested in the docs, but how will this affect reverse / url?
   # https://docs.djangoproject.com/en/dev/topics/http/urls/#notes-on-capturing-text-in-urls
    url(r'^(?P<campaign_id_short>[A-Za-z0-9]+)/$',
        'campaign_short', name='campaign_short'),
    url(r'^(?P<campaign_id_short>[A-Za-z0-9]+)/(?:(?P<mode>\w+).html)?$',
        'campaign_short', name='campaign_short'),
)
