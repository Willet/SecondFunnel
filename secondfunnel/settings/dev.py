from common import *

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
CONTENTGRAPH_BASE_URL = 'http://contentgraph-test.elasticbeanstalk.com/graph'
AWS_STORAGE_BUCKET_NAME = 'secondfunnel-test-static'
INTENTRANK_CONFIG_BUCKET_NAME = None

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'.format(WEBSITE_BASE_URL)
COMPRESS_URL = STATIC_URL

DEFAULT_FILE_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
COMPRESS_STORAGE = STATICFILES_STORAGE


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': ['127.0.0.1:11211']
    }
}

INSTALLED_APPS += (
    'django_nose',  # for testing...? we don't use it, but here it is
    'debug_toolbar',
)
# add "?prof" to profile the request:
# http://blueprintforge.com/blog/2012/01/24/measuring-optimising-database-performance-in-django/
MIDDLEWARE_CLASSES += (
    'snippetscream.ProfileMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # oddly enough, this goes *after* debug_toolbar
    'apps.utils.models.NonHtmlDebugToolbarMiddleware',
)

# force show toolbar
# http://stackoverflow.com/a/10518040/1558430
SHOW_TOOLBAR_CALLBACK = lambda: DEBUG
CONFIG_DEFAULTS = {  # Toolbar options
    'SHOW_COLLAPSED': True,
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# We should be able to just run `bundle exec sass` in dev as we do in
# production. Until we've figured that out, just running things this way
COMPRESS_PRECOMPILERS = (
    ('text/x-sass', 'sass {infile} {outfile}'),
    ('text/x-scss', 'sass {infile} {outfile}'),
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

GOOGLE_API_PRIVATE_KEY = 'google-service-account-prod.p12'
GOOGLE_SERVICE_ACCOUNT = '248578306350@developer.gserviceaccount.com'

BROKER_URL = 'amqp://guest:guest@localhost:5672//'
BROKER_TRANSPORT_OPTIONS = {

}

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
        # https://willet.atlassian.net/browse/CM-125
        'product-update-notification-queue-dev':
            {'queue_name': 'product-update-notification-queue-dev',
             'handler': 'handle_product_update_notification_message',
             'interval': 5},

        # https://willet.atlassian.net/browse/CM-126
        'content-update-notification-queue-dev':
            {'queue_name': 'content-update-notification-queue-dev',
             'handler': 'handle_content_update_notification_message',
             'interval': 5},

        # https://willet.atlassian.net/browse/CM-127
        'tile-generator-notification-queue-dev':
            {'queue_name': 'tile-generator-notification-queue-dev',
             'handler': 'handle_tile_generator_update_notification_message',
             'interval': 5},

        # https://willet.atlassian.net/browse/CM-128
        'ir-config-generator-notification-queue-dev':
            {'queue_name': 'ir-config-generator-notification-queue-dev',
             'handler': 'handle_ir_config_update_notification_message'},

        # https://willet.atlassian.net/browse/CM-124
        'scraper-notification-queue-dev':
            {'queue_name': 'scraper-notification-queue-dev',
             'handler': 'handle_scraper_notification_message'},

        'page-generator-dev':
            {'queue_name': 'page-generator-dev',
             'handler': 'handle_page_generator_notification_message'},
    }
}

TRACKING_COOKIE_AGE = 30  # seconds: 30 seconds
TRACKING_COOKIE_DOMAIN = None  # No need to set specific domain for local tests
