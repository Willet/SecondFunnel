from django.conf.urls import patterns, url

urlpatterns = patterns('apps.pinpoint.views',
    url(r'^admin/social-auth/connect/$', 'social_auth_redirect',
        name='social-auth-connect'),

    url(r'^admin/social-auth/disconnect/$', 'social_auth_redirect',
        name='social-auth-disconnect'),

    url(r'^admin/(?P<store_id>\d+)/delete_campaign/(?P<campaign_id>\d+)/$',
        'delete_campaign', name='delete-campaign-admin'),

    # As suggested in the docs, but how will this affect reverse / url?
    # https://docs.djangoproject.com/en/dev/topics/http/urls/#notes-on-capturing-text-in-urls
    url(r'^(?P<store_id>\d+)/(?P<campaign_id>\d+)/?$', 'campaign', name='campaign'),
    url(r'^(?P<store_id>\d+)/(?P<campaign_id>\d+)/(?:(?P<mode>\w+).html)?$', 'campaign', name='campaign'),
)
