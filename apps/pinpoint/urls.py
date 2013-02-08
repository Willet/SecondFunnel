from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('apps.pinpoint.views',
    url(r'^login/redirect/$', 'login_redirect', name='login-redirect'),

    url(r'^admin/$', 'admin', name='admin'),

    url(r'^admin/social-auth/$', 'social_auth', name='social-auth'),

    url(r'^admin/(?P<store_id>\d+)/$', 'store_admin', name='store-admin'),

    url(r'^admin/(?P<store_id>\d+)/asset-manager/$', 'asset_manager',
        name='asset-manager'),

    url(r'^admin/(?P<store_id>\d+)/asset-manager/tag_content$', 'tag_content',
        name='tag-content'),

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

    url(r'^(?P<campaign_id>\d+)/$', 'campaign', name='campaign'),
)

# AJAX
urlpatterns += patterns('apps.pinpoint.ajax',
    url(r'^ajax/campaign/save_draft/$',
        'campaign_save_draft', name='ajax-campaign-save-draft'),

    url(r'^ajax/campaign/publish/$',
        'campaign_publish', name='ajax-campaign-publish'),

    url(r'^ajax/upload_image/$',
        'upload_image', name='ajax-upload-image'),
)
