from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('apps.analytics.views',
    url(r'embedded/$', 'embedded_analytics',
        name='embedded-analytics'),
)

urlpatterns += patterns('apps.analytics.ajax',
    url(r'api/overview/$', 'analytics_overview',
        name='ajax-analytics-overview'),
)
