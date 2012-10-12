from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('apps.analytics.views',
    url(r'embedded/(?P<app_slug>[-\w]+)/$', 'embedded_analytics',
        name='embedded-analytics'),
)

urlpatterns += patterns('apps.analytics.ajax',
    url(r'api/(?P<app_slug>[-\w]+)/$', 'analytics_overview',
        name='ajax-analytics-overview'),
)
