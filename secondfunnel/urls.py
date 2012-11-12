from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from apps.assets.forms import HTMLPasswordResetForm

admin.autodiscover()

urlpatterns = patterns('',
    # INTERNAL ADMIN
    url(r'^admin/', include(admin.site.urls)),

    # APPS
    url(r'^pinpoint/', include('apps.pinpoint.urls')),
    url(r'^analytics/', include('apps.analytics.urls')),

    # APIs
    url(r'^api/assets/', include('apps.assets.api_urls')),

    # ACCOUNTS
    url(r'^accounts/login/$', 
        'django.contrib.auth.views.login',
        name="login"),

    url(r'^accounts/logout/$', 
        'django.contrib.auth.views.logout_then_login',
        name="logout"),

    url(r'^accounts/password/reset/$', 
        'django.contrib.auth.views.password_reset',
        {'template_name': 'registration/pass_reset_form.html',
            'email_template_name': 'registration/pass_reset_email.html',
            'subject_template_name': 'registration/pass_reset_email_subject.txt',
            'password_reset_form': HTMLPasswordResetForm,
            'post_reset_redirect': 'done/'},
        name="password_reset"),

    url(r'^accounts/password/reset/done/$', 
        'django.contrib.auth.views.password_reset_done',
        {'template_name': 'registration/pass_reset_done.html'},
        name="password_reset_done"),

    url(r'^accounts/reset/(?P<uidb36>[-\w]+)/(?P<token>[-\w]+)/$', 
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'registration/pass_reset_confirm.html'},
        name="password_reset_confirm"),

    url(r'^accounts/password/reset/complete/$', 
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'registration/pass_reset_complete.html'},
        name="password_reset_complete"),

    url(r'^accounts/password/change/$', 
        'django.contrib.auth.views.password_change',
        {'template_name': 'registration/pass_change.html'},
        name="password_change"),

    url(r'^accounts/password/change/done/$', 
        'django.contrib.auth.views.password_change_done',
        {'template_name': 'registration/pass_change_done.html'},
        name="password_change_done"),

    url(r'^accounts/profile/$', 
        'django.views.generic.simple.direct_to_template',
        {'template': 'registration/profile.html'},
        name="profile"),

    # WEBSITE
    url(r'^', include('apps.website.urls')),
)

urlpatterns += staticfiles_urlpatterns()
