from django.conf.urls import url, patterns

urlpatterns = patterns(
    'apps.scrapy.views',
    url(r'^$', 'index'),
    url(r'^(?P<page_slug>[-\w]+)/$', 'page'),
    url(r'^(?P<page_slug>[-\w]+)/result/(?P<job_id>.+)/$', 'result'),

    url(r'^(?P<page_slug>[-\w]+)/scrape', 'scrape'),
    url(r'^(?P<page_slug>[-\w]+)/prioritize', 'prioritize'),
)
