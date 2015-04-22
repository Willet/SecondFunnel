from django.conf.urls import url, patterns

urlpatterns = patterns(
    'apps.scrapy.views',
    url(r'^$', 'index'),
    url(r'^(?P<page_slug>[-\w]+)/$', 'page'),
    url(r'^(?P<page_slug>[-\w]+)/log$', 'log'),
    url(r'^(?P<page_slug>[-\w]+)/log/(?P<job_id>.+)/$', 'log'),
    url(r'^(?P<page_slug>[-\w]+)/summary$', 'summary'),
    url(r'^(?P<page_slug>[-\w]+)/summary/(?P<job_id>.+)$', 'summary'),

    url(r'^(?P<page_slug>[-\w]+)/scrape', 'scrape'),
    url(r'^(?P<page_slug>[-\w]+)/prioritize', 'prioritize'),
)
