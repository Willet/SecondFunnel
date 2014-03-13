# Apparently, it is not possible to import two levels deep in Django?
# Copied from `production.py`

from common import *
from secondfunnel.errors import EnvironmentSettingsError

if not all([AWS_STORAGE_BUCKET_NAME, MEMCACHED_LOCATION]):
    raise EnvironmentSettingsError()

DEBUG = False
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

# Enable GZIP and Minification
COMPRESS = True
COMPRESS_VERSION = True
COMPRESS_ENABLED = True

AWS_IS_GZIPPED = True
AWS_HEADERS =  {
    'Expires': BROWSER_CACHE_EXPIRATION_DATE,
    'Cache-Control': "public, max-age=604800",
    'Vary': 'Accept-Encoding',
}

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
# TODO: test CM instances currently handle messages from production
# Scraper / TileConfigGen / IRConfigGen workers, and MUST be swapped to
# test queues if production CM worker is deployed
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
        # https://willet.atlassian.net/browse/CM-125
        'product-update-notification-queue-demo':
            {'queue_name': 'product-update-notification-queue-demo',
             'handler': 'handle_product_update_notification_message',
             'interval': 300},

        # https://willet.atlassian.net/browse/CM-126
        'content-update-notification-queue-demo':
            {'queue_name': 'content-update-notification-queue-demo',
             'handler': 'handle_content_update_notification_message',
             'interval': 300},

        # https://willet.atlassian.net/browse/CM-127
        'tile-generator-notification-queue-demo':
            {'queue_name': 'tile-generator-notification-queue-demo',
             'handler': 'handle_tile_generator_update_notification_message',
             'interval': 5},

        # https://willet.atlassian.net/browse/CM-128
        'ir-config-generator-notification-queue-demo':
            {'queue_name': 'ir-config-generator-notification-queue-demo',
             'handler': 'handle_ir_config_update_notification_message'},

        # https://willet.atlassian.net/browse/CM-124
        'scraper-notification-queue-demo':
            {'queue_name': 'scraper-notification-queue-demo',
             'handler': 'handle_scraper_notification_message'},

        'page-generator-demo':
            {'queue_name': 'page-generator-demo',
             'handler': 'handle_page_generator_notification_message'},
    }
}

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
COMPRESS_URL = 'http://%s/' % CLOUDFRONT_DOMAIN

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': MEMCACHED_LOCATION
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

GOOGLE_ANALYTICS_PROFILE = '67271131'
GOOGLE_ANALYTICS_PROPERTY = 'UA-23764505-15'

GOOGLE_API_PRIVATE_KEY = 'google-service-account-prod.p12'
GOOGLE_SERVICE_ACCOUNT = '248578306350@developer.gserviceaccount.com'

BROKER_URL = 'sqs://%s:%s@' % (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
BROKER_TRANSPORT_OPTIONS = {
    'region': 'us-west-1',
    'visibility_timeout': 30,
    'polling_interval': 1,
    'queue_name_prefix': 'celery-',
    }

# Useful when testing, as there is no distinction between the test env and
# the live environment at the moment

# Nick's other test instagram client; good for secondfunnel-test
# INSTAGRAM_CLIENT_ID = '3fc578b28e2a4b43a51ea2fa735599fd'
# INSTAGRAM_CLIENT_SECRET = '1e12ec8c92304cd28582df05ab430762'

INSTAGRAM_CLIENT_ID = 'be95027932f64f4aaa465ffed160a8fb'
INSTAGRAM_CLIENT_SECRET = 'aac059c1acb341d3b44b9139dc106dbe'
