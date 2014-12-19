from django.conf.urls import url, patterns

urlpatterns = patterns(
    'apps.scrapy.views',
    url(r'^$', 'index'),
    url(r'^(?P<store_slug>[-\w]+)/$', 'store'),
    url(r'^(?P<store_slug>[-\w]+)/log$', 'log'),
    url(r'^(?P<store_slug>[-\w]+)/log/(?P<filename>.+)/$', 'log'),
    url(r'^(?P<store_slug>[-\w]+)/summary$', 'summary'),
    url(r'^(?P<store_slug>[-\w]+)/summary/(?P<filename>.+)$', 'summary'),

    url(r'^(?P<store_slug>[-\w]+)/scrape', 'scrape'),
)