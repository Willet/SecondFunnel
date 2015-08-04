from django.conf.urls import url, patterns

urlpatterns = patterns(
    'apps.scrapy.views',
    url(r'^$', 'index'),
    url(r'^(?P<page_slug>[-\w]+)/?$', 'page'),
    url(r'^(?P<page_slug>[-\w]+)/scrape/?$', 'scrape'),
    url(r'^(?P<page_slug>[-\w]+)/prioritize/?$', 'prioritize'),
    url(r'^(?P<page_slug>[-\w]+)/log/?$', 'log'),
    url(r'^(?P<page_slug>[-\w]+)/log/(?P<filename>.+)/?$', 'log'),
    url(r'^(?P<page_slug>[-\w]+)/summary/?$', 'summary'),
    url(r'^(?P<page_slug>[-\w]+)/summary/(?P<filename>.+)/?$', 'summary'),
)
