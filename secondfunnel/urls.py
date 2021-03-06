from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^healthcheck/?$', 'apps.utils.views.healthcheck'),

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
    url(r'^scrapy$', lambda x: HttpResponseRedirect('scrapy/')),
    url(r'^scrapy/', include('apps.scrapy.urls')),
    url(r'^tracker/', include('apps.tracking.urls')),
    url(r'^dashboard$', lambda x: HttpResponseRedirect('/dashboard/')),
    url(r'^dashboard/', include('apps.dashboard.urls')),
    url(r'^api2/', include('apps.api2.urls')),


    url(r'^(?P<page_slug>[^/\.]+)/?$',
        'apps.light.views.landing_page'),

    # special top-level urls for RSS feeds
    url(r'^(?P<page_id>\d+)/(?P<feed_name>[^/\.]+\.rss)$',
        'apps.intentrank.views.get_rss_feed', name='get-feed'),
    url(r'^(?P<page_slug>[^/\.]+)/(?P<feed_name>[^/\.]+\.rss)$',
        'apps.intentrank.views.get_rss_feed'),
    url(r'^(?P<page_slug>[^/\.]+)/google\.rss$',
        'apps.intentrank.views.get_rss_feed'),

    # page  livedin/id/123
    url(r'^(?P<page_slug>[^/\.]+)'
        r'/(?P<identifier>(id|sku|tile|category|preview))'
        r'/(?P<identifier_value>[\w\.\|-]+)/?$',
        'apps.light.views.landing_page'),
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
