from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('apps.pinpoint.views',
    url(r'^admin/$', 'admin', name='admin'),

    url(r'^admin/(?P<store_id>\d+)/$', 'store_admin', name='store-admin'),

    url(r'^admin/(?P<campaign_id>\d+)/analytics/$',
        'campaign_analytics_admin', name='analytics-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/analytics/$',
        'store_analytics_admin', name='analytics-store-admin'),

    url(r'^admin/(?P<store_id>\d+)/new_campaign/$',
        'new_campaign', name='new-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/new_campaign/(?P<campaign_id>\d+)/confirm/$',
        'confirm_new_campaign', name='confirm-new-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/edit_campaign/(?P<campaign_id>\d+)/$',
        'edit_campaign', name='edit-campaign-admin'),

    url(r'^admin/(?P<store_id>\d+)/new_campaign/(?P<block_type_id>\d+)/$',
        'block_type_router', name='block-type-wizard'),

    url(r'^(?P<campaign_id>\d+)/$', 'campaign', name='campaign'),

    url(r'^generic/(?P<product_id>\d+)/$',
        'generic_page',name='pinpoint_generic'),
)

# AJAX
urlpatterns += patterns('apps.pinpoint.ajax',
    url(r'^ajax/campaign/save_draft/$',
        'campaign_save_draft', name='ajax-campaign-save-draft'),

    url(r'^ajax/campaign/publish/$',
        'campaign_publish', name='ajax-campaign-publish'),
)
