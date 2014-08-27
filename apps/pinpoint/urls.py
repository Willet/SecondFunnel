from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.pinpoint.views',

    url(r'^admin/social-auth/connect/$', 'social_auth_redirect',
        name='social-auth-connect'),

    url(r'^admin/social-auth/disconnect/$', 'social_auth_redirect',
        name='social-auth-disconnect'),

    url(r'^/?$', 'get_overview'),
)
