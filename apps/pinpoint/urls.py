from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    url(r'^login/$', 
        'django.contrib.auth.views.login',
        {'template_name': 'login/login.html'})
)

urlpatterns += patterns('apps.pinpoint.views',
    url(r'(?P<campaign_id>\d+)/admin/$', 'pinpoint_admin', name='pinpoint_admin'),
    url(r'generic/(?P<product_id>\d+)/$', 'generic_page', name='pinpoint_generic'),
    url(r'(?P<campaign_id>\d+)/$', 'campaign', name='campaign'),
)
