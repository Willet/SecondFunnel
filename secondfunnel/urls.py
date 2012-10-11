from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    # API
    url(r'^api/assets/', include('apps.assets.api_urls')),

    # ANALYTICS
    url(r'^', include('apps.analytics.urls')),
)

urlpatterns += staticfiles_urlpatterns()
