from django.conf import settings
from django.conf.urls import patterns, url
from django.http import HttpResponsePermanentRedirect

urlpatterns = patterns('apps.website.urls',
    url(
        r'^$',
        lambda x: HttpResponsePermanentRedirect(settings.WEBSITE_BASE_URL),
        name='website-index'
    ),
    url(
        r'^about$',
        lambda x: HttpResponsePermanentRedirect('%s/about' % settings.WEBSITE_BASE_URL),
        name='website-about'
    ),
    url(
        r'^contact$',
        lambda x: HttpResponsePermanentRedirect('%s/contact' % settings.WEBSITE_BASE_URL),
        name='website-contact'
    ),
    url(
        r'^why$',
        lambda x: HttpResponsePermanentRedirect('%s/why' % settings.WEBSITE_BASE_URL),
        name='website-why'
    ),
)