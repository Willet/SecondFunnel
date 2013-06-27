from django.conf.urls import patterns, url

# url prefix: /analytics/

urlpatterns = patterns('apps.analytics.ajax',
    url(r'api/pinpoint/$', 'analytics_pinpoint', name='ajax-analytics-pinpoint'),
)
