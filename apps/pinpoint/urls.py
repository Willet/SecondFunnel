from django.conf.urls import patterns, url

urlpatterns = patterns('apps.pinpoint.views',
    url(r'^login/redirect/$', 'login_redirect', name='login-redirect'),

    url(r'^admin/$', 'admin', name='admin'),

    url(r'^admin/social-auth/connect/$', 'social_auth_redirect',
        name='social-auth-connect'),

    url(r'^admin/social-auth/disconnect/$', 'social_auth_redirect',
        name='social-auth-disconnect'),

    url(r'^admin/(?P<store_id>\d+)/$', 'store_admin', name='store-admin'),

    url(r'^admin/(?P<store_id>\d+)/asset-manager/$', 'asset_manager',
        name='asset-manager'),

    url(r'^admin/(?P<store_id>\d+)/asset-manager/upload/$', 'upload_asset',
        name='upload-asset'),

    url(r'^admin/(?P<store_id>\d+)/(?P<campaign_id>\d+)/analytics/$',
        'campaign_analytics_admin', name='analytics-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/analytics/$',
        'store_analytics_admin', name='analytics-store-admin'),

    url(r'^admin/(?P<store_id>\d+)/new_campaign/$',
        'new_campaign', name='new-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/edit_campaign/(?P<campaign_id>\d+)/$',
        'edit_campaign', name='edit-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/delete_campaign/(?P<campaign_id>\d+)/$',
        'delete_campaign', name='delete-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/new_campaign/(?P<block_type_id>\d+)/$',
        'block_type_router', name='block-type-wizard'),

    # As suggested in the docs, but how will this affect reverse / url?
    # https://docs.djangoproject.com/en/dev/topics/http/urls/#notes-on-capturing-text-in-urls
    url(r'^(?P<campaign_id>\d+)/$', 'campaign', name='campaign'),
    url(r'^(?P<campaign_id>\d+)/(?:(?P<mode>\w+).html)?$', 'campaign', name='campaign'),
)

# @deprecated (AJAX)
urlpatterns += patterns('apps.pinpoint.ajax',
    url(r'^ajax/upload_image/$',
        'ajax_upload_image', name='ajax-upload-image'),
)
