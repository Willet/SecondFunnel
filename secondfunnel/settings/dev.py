from common import *

# Optional private local settings
try:
    from local import *
except:
    pass

ENVIRONMENT = "dev"
DEBUG = True
TEMPLATE_DEBUG = DEBUG


INTERNAL_IP = '127.0.0.1:8000'
INTERNAL_IPS = ('localhost',  # virtualenv
                '127.0.0.1',  # virtualenv
                '10.0.1.1',  # vagrant
                '10.0.2.2',
                '24.137.221.230',  # waterloo office
                '10.217.146.216',  # the elastic load balancer (I think)
                INTERNAL_IP)

WEBSITE_BASE_URL = ''.format(INTERNAL_IP)
INTENTRANK_BASE_URL = WEBSITE_BASE_URL
AWS_STORAGE_BUCKET_NAME = 'secondfunnel-test-static'
INTENTRANK_CONFIG_BUCKET_NAME = None

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'.format(WEBSITE_BASE_URL)
COMPRESS_URL = STATIC_URL

DEFAULT_FILE_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
COMPRESS_STORAGE = STATICFILES_STORAGE

# Uncomment this line if you want to not log sql
#DEVSERVER_MODULES = ()

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': ['127.0.0.1:11211']
    }
}

INSTALLED_APPS += (
    'django_nose', # must be added after south
    'debug_toolbar',
    'devserver',
)
# add "?prof" to profile the request:
# http://blueprintforge.com/blog/2012/01/24/measuring-optimising-database-performance-in-django/
MIDDLEWARE_CLASSES += (
    'snippetscream.ProfileMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'apps.utils.middleware.NonHtmlDebugToolbarMiddleware', # *after* debug_toolbar
    'apps.utils.middleware.ShowHandlerMiddleware',
    'devserver.middleware.DevServerMiddleware',
    'apps.light.middleware.BrowserSyncMiddleware',
)

# force show toolbar
# http://stackoverflow.com/a/10518040/1558430
SHOW_TOOLBAR_CALLBACK = lambda: DEBUG
CONFIG_DEFAULTS = {  # Toolbar options
    'SHOW_COLLAPSED': True,
}
# Fixes "ImproperlyConfigured" error for wsgi
# https://github.com/django-debug-toolbar/django-debug-toolbar/issues/521
try:
    if sys.argv[1] == 'runserver' or sys.argv[1] == 'runserver_plus':
        DEBUG_TOOLBAR_PATCH_SETTINGS = DEBUG
    else:
        DEBUG_TOOLBAR_PATCH_SETTINGS = False
except IndexError:
        DEBUG_TOOLBAR_PATCH_SETTINGS = False

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# We should be able to just run `bundle exec sass` in dev as we do in
# production. Until we've figured that out, just running things this way
COMPRESS_PRECOMPILERS = (
    ('text/x-sass', 'sass {infile} {outfile}'),
    ('text/x-scss', 'sass {infile} {outfile}'),
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

GOOGLE_SERVICE_ACCOUNT = '248578306350@developer.gserviceaccount.com'

BROKER_URL = 'amqp://guest:guest@localhost:5672//'
BROKER_TRANSPORT_OPTIONS = {

}

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# dict of queues by region to poll regularly, using celery beat.
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
    }
}

TRACKING_COOKIE_AGE = 30  # seconds: 30 seconds
TRACKING_COOKIE_DOMAIN = None  # No need to set specific domain for local tests

KEEN_CONFIG = {
    'projectId': '532745f6ce5e4326bf000011',
    'writeKey': '0cb6ca2eff48d4ff58e2fdcd6ddd0d6fc5f09d58241dd007f68d434ed47ddde33ad76ead3d1e6aca30022e704e36dd46bf443862b7077819e42bb16856beb1ca6751f5d180a2a65e0b2265c9145aabbf722c6935e9879c9031c23692124f41c6134c1cd648d0ba0d13b8df432aa6e8c8',
    'readKey': 'c8ff6b6ec8efb33e85fbcade3d9ecbe102dbb884c586ab4cf7b14e0014effdc911e819b6ba9cb7517c3fbe26a5cf2812ff9cafe29b9d073e8a50928cf27f85b5845c7ba3c304d8b7dc346200dce3eecfe13d541c6bcddbdc3f70c6213a4f18f5c66de9f22ae62b1e107cc27252314db8'
}

PREDICTION_IO_API_KEY = "6n6hcmCc8IDI0sfOCMdmEp9jig4aIN23dmPAWBl5dBOkiyzBjZTMPHQTJRjO0cdG"
