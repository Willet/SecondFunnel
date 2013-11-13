from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.http import HttpResponse

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^healthcheck/$', lambda x: HttpResponse('OK', status=200)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^graph/', include('apps.api.urls')),
)
