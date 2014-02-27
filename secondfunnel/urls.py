from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^healthcheck/$', lambda x: HttpResponse('OK', status=200)),

    # INTERNAL ADMIN
    url(r'^admin/', include(admin.site.urls)),

    # APPS
    # Which apps do we need to keep enabled to keep old pages working?
    url(r'^pinpoint/', include('apps.pinpoint.urls')),
    #url(r'p/', include('apps.pinpoint.global_urls')),
    url(r'^intentrank/', include('apps.intentrank.urls')),

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

handler500 = 'apps.pinpoint.views.app_exception_handler'
