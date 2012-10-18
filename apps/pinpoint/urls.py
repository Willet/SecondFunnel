from django.conf.urls.defaults import patterns, url
from django.contrib.auth.views import login

urlpatterns = patterns('',
    url(r'^login/$', 
        login, 
        {'template_name': 'login/login.html'})
)

urlpatterns += patterns('apps.pinpoint.views',
    url(r'(?P<campaign_id>\d+)/admin/$', 'pinpoint_admin', name='pinpoint_admin'),
    url(r'generic/(?P<product_id>\d+)/$', 'generic_page', name='pinpoint_generic'),
    url(r'(?P<campaign_id>\d+)/$', 'campaign', name='campaign'),
)
