from django.conf import settings
from django.conf.urls import patterns, url
from django.http import HttpResponsePermanentRedirect

urlpatterns = patterns('apps.website.urls',
    url(
        r'^$',
        lambda x: HttpResponsePermanentRedirect('http://www.secondfunnel.com'),
        name='website-index'
    ),
)
