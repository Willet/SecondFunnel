from django.conf import settings
from django.conf.urls import patterns, url
from django.http import HttpResponsePermanentRedirect

# remove pointless infinite loops
if settings.ENVIRONMENT == "dev":
    WEBSITE_BASE_URL = 'http://www.secondfunnel.com'
else:
    WEBSITE_BASE_URL = settings.WEBSITE_BASE_URL

urlpatterns = patterns('apps.website.urls',
    url(
        r'^$',
        lambda x: HttpResponsePermanentRedirect(WEBSITE_BASE_URL),
        name='website-index'
    ),
    url(
        r'^about$',
        lambda x: HttpResponsePermanentRedirect('%s/about' % WEBSITE_BASE_URL),
        name='website-about'
    ),
    url(
        r'^contact$',
        lambda x: HttpResponsePermanentRedirect('%s/contact' % WEBSITE_BASE_URL),
        name='website-contact'
    ),
    url(
        r'^why$',
        lambda x: HttpResponsePermanentRedirect('%s/why' % WEBSITE_BASE_URL),
        name='website-why'
    ),
)