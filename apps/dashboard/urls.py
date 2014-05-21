from django.conf.urls import patterns, url
from django.http import HttpResponse

urlpatterns = patterns('apps.dashboard.views',
                       url(r'^$', 'summerloves', name="index"),
)