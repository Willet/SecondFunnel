from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from apps.assets.forms import HTMLPasswordResetForm

admin.autodiscover()

urlpatterns = patterns('',
    url(r'', include('social_auth.urls')),

    url(r'^healthcheck/$', lambda x: HttpResponse('OK', status=200)),

    # INTERNAL ADMIN
    url(r'^admin/', include(admin.site.urls)),

    # APPS
    url(r'^pinpoint/', include('apps.pinpoint.urls')),
    url(r'p/', include('apps.pinpoint.global_urls')),
    url(r'^analytics/', include('apps.analytics.urls')),
    url(r'^intentrank/', include('apps.intentrank.urls')),

    # APIs
    url(r'^api/assets/', include('apps.assets.api_urls')),

    # ACCOUNTS
    url(r'^accounts/login/$',
        'apps.pinpoint.views.login_success_redirect',
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

if settings.DEBUG:
    # Used for local development; removes the need to run collectstatic in the
    # dev environment.
    urlpatterns += patterns('django.contrib.staticfiles.views',
         url(r'^static/(?P<path>.*)$', 'serve'),
    )

handler500 = 'apps.pinpoint.views.app_exception_handler'
