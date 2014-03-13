from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^healthcheck/$', lambda x: HttpResponse('OK', status=200)),

    # INTERNAL ADMIN
    url(r'^admin/?', include(admin.site.urls)),

    # APPS
    url(r'^assets/', include('apps.assets.urls')),
    url(r'^pinpoint/', include('apps.pinpoint.urls')),
    #url(r'p/', include('apps.pinpoint.global_urls')),
    url(r'^intentrank/', include('apps.intentrank.urls')),
    url(r'^tracker/', include('apps.tracking.urls')),

    # special top-level urls for RSS feeds
    url(r'^(?P<page_slug>[^/\.]+)/?$',
        'apps.pinpoint.views.campaign_by_slug', name='get-page-by-slug'),
    # special top-level urls for RSS feeds
    url(r'^(?P<page_id>\d+)/(?P<feed_name>[^/\.]+\.rss)$',
        'apps.intentrank.views.get_rss_feed', name='get-feed'),
    url(r'^(?P<page_slug>[^/\.]+)/(?P<feed_name>[^/\.]+\.rss)$',
        'apps.intentrank.views.get_rss_feed', name='get-feed'),

    # APIs
    url(r'^contentgraph/', include('apps.contentgraph.urls')),
    url(r'^static_pages/', include('apps.static_pages.urls')),
    url(r'^api/assets/', include('apps.assets.api_urls')),
    url(r'^graph/', include('apps.api.urls')),

    # WEBSITE
    url(r'^$', include('apps.website.urls')),
)

if settings.DEBUG:
    # Used for local development; removes the need to run collectstatic in the
    # dev environment.
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )

    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

handler500 = 'apps.pinpoint.views.app_exception_handler'
