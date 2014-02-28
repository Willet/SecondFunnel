from django.conf import settings
from django.conf.urls import patterns, url
from django.http import HttpResponsePermanentRedirect

# remove pointless infinite loops
if settings.ENVIRONMENT == "dev":
    WEBSITE_BASE_URL = 'http://www.secondfunnel.com'
else:
    WEBSITE_BASE_URL = settings.WEBSITE_BASE_URL

urlpatterns = patterns('apps.website.views',
    url(r'^(?P<page_id>\d+)/(?P<feed_name>[^/\.]+\.rss)$', 'get_rss_feed',
        name='get-feed'),
    url(r'^(?P<page_slug>[^/\.]+)/(?P<feed_name>[^/\.]+\.rss)$', 'get_rss_feed',
        name='get-feed'),
    url(
        r'^$',
        lambda x: HttpResponsePermanentRedirect(WEBSITE_BASE_URL),
        name='website-index'
    ),
)
