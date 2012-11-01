from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('apps.analytics.ajax',
    url(r'api/pinpoint/$', 'analytics_pinpoint', name='ajax-analytics-pinpoint'),
)
