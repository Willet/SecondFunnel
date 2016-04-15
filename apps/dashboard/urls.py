from django.conf.urls import patterns, url

urlpatterns = patterns(
    'apps.dashboard.views',
    url(r'^$', 'index', name="index"),
    url(r'^login', 'user_login', name='login'),
    url(r'^logout', 'user_logout', name='logout'),
    url(r'^overview', 'overview', name='overview'),
    #url(r'^register', 'user_registration', name='register'),
    url(r'retrieve-data', 'get_data', name="get_data"),    
    url(r'^(?P<dashboard_slug>[-\w]+)/scrape', 'scrape', name='scrape'),
    url(r'^(?P<dashboard_slug>[-\w]+)/products', 'dashboard_products', name='dashboard_products'),
    #url(r'^(?P<dashboard_slug>[-\w]+)/tiles', 'dashboard_tiles', name='dashboard_tiles'),
    url(r'^(?P<dashboard_slug>[-\w]+)', 'dashboard_tiles', name='dashboard'),
)
