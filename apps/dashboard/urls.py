from django.conf.urls import patterns, url
from django.http import HttpResponse

urlpatterns = patterns('apps.dashboard.views',
                       url(r'^$', 'gap', name="index"),
                       url(r'^gap', 'gap', name="gap"),
                       url(r'retrieve-data', 'get_data', name="get_data"),
)
