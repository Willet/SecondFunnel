from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^healthcheck/?$', lambda x: HttpResponse('OK', status=200)),

    # INTERNAL ADMIN
    url(r'^admin$', lambda x: HttpResponseRedirect("/admin/")),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {"template_name": 'admin/login.html'}),

    # PUBLIC WEBSITE
    url(r'^showcase/?$', include('apps.website.urls')),
    url(r'^features/video/?$', include('apps.website.urls')),
    url(r'^showcase/?$', include('apps.website.urls')),
    url(r'^contact/?$', include('apps.website.urls')),

    # APPS
    url(r'^assets/', include('apps.assets.urls')),
    url(r'^ads/(?P<page_id>[-\w]+)/?$', 'apps.light.views.ad_banner'),
    url(r'^imageservice/', include('apps.imageservice.urls')),
    url(r'^intentrank/', include('apps.intentrank.urls')),
    url(r'^scraper/', include('apps.scraper.urls')),
    url(r'^tracker/', include('apps.tracking.urls')),
    # dashboard
    url(r'^dashboard$', lambda x: HttpResponseRedirect('/dashboard/')),
    url(r'^dashboard/', include('apps.dashboard.urls')),

    url(r'^(?P<page_slug>[^/\.]+)/?$',
        'apps.light.views.landing_page'),

    # special top-level urls for RSS feeds
    url(r'^(?P<page_id>\d+)/(?P<feed_name>[^/\.]+\.rss)$',
        'apps.intentrank.views.get_rss_feed', name='get-feed'),
    url(r'^(?P<page_slug>[^/\.]+)/(?P<feed_name>[^/\.]+\.rss)$',
        'apps.intentrank.views.get_rss_feed'),
    url(r'^(?P<page_slug>[^/\.]+)/google\.rss$',
        'apps.intentrank.views.get_rss_feed'),
    # shop-the-look slugs e.g. livedin/id/123
    url(r'^(?P<page_slug>[^/\.]+)'
        r'/(?P<identifier>(id|sku|tile))'
        r'/(?P<identifier_value>\w+)/?$',
        'apps.light.views.landing_page'),

    # APIs
    url(r'^contentgraph/', include('apps.contentgraph.urls')),
    url(r'^graph/', include('apps.api.urls')),
)

if settings.DEBUG:
    # Used for local development; removes the need to run collectstatic in the
    # dev environment.
    urlpatterns += patterns(
        'django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )

    import debug_toolbar
    urlpatterns += patterns(
        '',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )

urlpatterns += patterns('',
    # WEBSITE
    url(r'^(.*)$', include('apps.website.urls'))
)
