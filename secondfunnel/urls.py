from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # INTERNAL ADMIN
    url(r'^admin/', include(admin.site.urls)),

    # APPS
    url(r'^pinpoint/', include('apps.pinpoint.urls')),
    url(r'^analytics/', include('apps.analytics.urls')),

    # APIs
    url(r'^api/assets/', include('apps.assets.api_urls')),

    # Accounts
    url(r'^accounts/login/$', 
        'django.contrib.auth.views.login',
        {'template_name': 'accounts/login.html'},
        name="login"),

    url(r'^accounts/logout/$', 
        'django.contrib.auth.views.logout',
        {'template_name': 'accounts/logout.html'},
        name="logout"),
)

urlpatterns += staticfiles_urlpatterns()
