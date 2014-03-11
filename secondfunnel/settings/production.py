from common import *
from secondfunnel.errors import EnvironmentSettingsError

if not all([AWS_STORAGE_BUCKET_NAME, MEMCACHED_LOCATION]):
    raise EnvironmentSettingsError()

ENVIRONMENT = "production"
DEBUG = False
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

# Enable GZIP and Minification
COMPRESS = True
COMPRESS_VERSION = True
COMPRESS_ENABLED = True

AWS_IS_GZIPPED = True
AWS_S3_CUSTOM_DOMAIN = CLOUDFRONT_DOMAIN
AWS_S3_SECURE_URLS = False
AWS_HEADERS =  {
    'Expires': BROWSER_CACHE_EXPIRATION_DATE,
    'Cache-Control': "public, max-age=604800",
    'Vary': 'Accept-Encoding',
}

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
        # https://willet.atlassian.net/browse/CM-125
        'product-update-notification-queue':
            {'queue_name': 'product-update-notification-queue',
             'handler': 'handle_product_update_notification_message',
             'interval': 300},

        # https://willet.atlassian.net/browse/CM-126
        'content-update-notification-queue':
            {'queue_name': 'content-update-notification-queue',
             'handler': 'handle_content_update_notification_message',
             'interval': 300},

        # https://willet.atlassian.net/browse/CM-127
        'tile-generator-notification-queue':
            {'queue_name': 'tile-generator-notification-queue',
             'handler': 'handle_tile_generator_update_notification_message',
             'interval': 5},

        # https://willet.atlassian.net/browse/CM-128
        'ir-config-generator-notification-queue':
            {'queue_name': 'ir-config-generator-notification-queue',
             'handler': 'handle_ir_config_update_notification_message'},

        # https://willet.atlassian.net/browse/CM-124
        'scraper-notification-queue':
            {'queue_name': 'scraper-notification-queue',
             'handler': 'handle_scraper_notification_message'},

        'page-generator':
            {'queue_name': 'page-generator',
             'handler': 'handle_page_generator_notification_message'},
    }
}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',

    # external apps
    'djcelery',
    'storages',
    'south',
    'django_extensions',
    'tastypie',
    'ajax_forms',
    'compressor',
    'maintenancemode',
    'social_auth',
    'corsheaders',

    # our apps
    'apps.api',
    'apps.assets',
    'apps.pinpoint',
    'apps.intentrank',
    'apps.contentgraph',
    'apps.website',
    'apps.static_pages',
    'apps.utils',
)

# contentgraph.el... contains nothing. fetch objects from the test db.
# uncomment if necessary.
CONTENTGRAPH_BASE_URL = 'http://contentgraph-test.elasticbeanstalk.com/graph'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = 'http://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
COMPRESS_URL = STATIC_URL

STALE_TILE_QUEUE_NAME = 'tileservice-worker-queue'

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
    'region': 'us-west-2',
    'visibility_timeout': 3600,  # 1 hour. (Possible fix for recurring tasks issue on SQS)
    'polling_interval': 1,
    'queue_name_prefix': 'celery-',
}
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

SESSION_COOKIE_DOMAIN = '.secondfunnel.com'

INSTAGRAM_CLIENT_ID = 'be95027932f64f4aaa465ffed160a8fb'
INSTAGRAM_CLIENT_SECRET = 'aac059c1acb341d3b44b9139dc106dbe'

TUMBLR_CONSUMER_KEY = 'Kr9rF0bykYZ2J2ncURUkwG0BBAEaDy7VGGzWZnVjna0bKPbRTn'
TUMBLR_CONSUMER_SECRET = 'aLK2zeDeTbITx03iFSPntIBRV9EIel6pl2Sp9ARbyMIEykGHXF'

GOOGLE_OAUTH2_CLIENT_ID = '218187505707-usif3u64gdr68rposjubk4461elk1e5c.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = 'O_C-_zo1dXQQkg989-LwJNbt'
