from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.dashboard.views',
    url(r'^$', 'index', name="index"),
    url(r'^login', 'user_login', name='login'),
    url(r'^logout', 'user_logout', name='logout'),
    url(r'^overview', 'overview', name='overview'),
    # url(r'^register', 'user_registration', name='register'),
    url(r'retrieve-data', 'get_data', name="get_data"),
    url(r'^(?P<dashboard_slug>[-\w]+)/upload', 'upload', name='upload'),
    url(r'^(?P<dashboard_slug>[-\w]+)/scrape', 'scrape', name='scrape'),
    url(r'^(?P<dashboard_slug>[-\w]+)', 'dashboard_tiles', name='dashboard'),
)
