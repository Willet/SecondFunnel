from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('apps.analytics.views',
    url(r'^analytics/embedded/(?P<app_slug>[-\w]+)/$', 'embedded_analytics',
        name='embedded-analytics'),
)

urlpatterns += patterns('apps.analytics.ajax',
    url(r'^analytics/api/(?P<app_slug>[-\w]+)/$', 'analytics_overview',
        name='ajax-analytics-overview'),
)
