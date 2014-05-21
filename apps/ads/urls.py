from django.conf.urls import patterns, url

urlpatterns = patterns('apps.ads.views',
    url(r'^(?P<page_id>\d+)/?$', 'campaign'),
)
