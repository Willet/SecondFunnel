from common import *

ENVIRONMENT = "test"
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Enable GZIP and Minification
COMPRESS = True
COMPRESS_VERSION = True
COMPRESS_ENABLED = True

AWS_IS_GZIPPED = True # GZip Middleware isn't recognized without this line because http://stackoverflow.com/a/19180415/1558430
AWS_S3_CUSTOM_DOMAIN = CLOUDFRONT_DOMAIN
AWS_S3_SECURE_URLS = False
AWS_HEADERS =  {
    'Expires': BROWSER_CACHE_EXPIRATION_DATE,
    'Cache-Control': "public, max-age=1800",
    'Vary': 'Accept-Encoding',
}

WEBSITE_BASE_URL = 'http://tng-test.secondfunnel.com'
INTENTRANK_BASE_URL = WEBSITE_BASE_URL
CONTENTGRAPH_BASE_URL = 'http://contentgraph-test.elasticbeanstalk.com/graph'
AWS_STORAGE_BUCKET_NAME = os.getenv('TestBucket', 'elasticbeanstalk-us-east-1-056265713214')
INTENTRANK_CONFIG_BUCKET_NAME = 'intentrank-config-test'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'.format(WEBSITE_BASE_URL)
COMPRESS_URL = 'http://%s/' % CLOUDFRONT_DOMAIN

# or '.elasticbeanstalk.com'
SESSION_COOKIE_DOMAIN = '.secondfunnel.com'

STALE_TILE_QUEUE_NAME = 'tileservice-worker-queue'

MEMCACHED_LOCATION = 'secondfunnel-test.yz4kz2.cfg.usw2.cache.amazonaws.com:11211'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': MEMCACHED_LOCATION
    }
}

INSTALLED_APPS += (
    'raven.contrib.django.raven_compat',  # logging
)

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

GOOGLE_API_PRIVATE_KEY = 'google-service-account-prod.p12'
GOOGLE_SERVICE_ACCOUNT = '248578306350@developer.gserviceaccount.com'

BROKER_URL = 'sqs://%s:%s@' % (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
BROKER_TRANSPORT_OPTIONS = {
    'region': 'us-west-2',
    'visibility_timeout': 3600,  # 1 hour. (Possible fix for recurring tasks issue on SQS)
    'polling_interval': 1,
    'queue_name_prefix': 'celery-test-',
}

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
        # https://willet.atlassian.net/browse/CM-125
        'product-update-notification-queue':
            {'queue_name': 'product-update-notification-queue',
             'handler': 'handle_product_update_notification_message',
             'interval': 5},

        # https://willet.atlassian.net/browse/CM-126
        'content-update-notification-queue':
            {'queue_name': 'content-update-notification-queue',
             'handler': 'handle_content_update_notification_message',
             'interval': 5},

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

        'page-generator-test':
            {'queue_name': 'page-generator-test',
             'handler': 'handle_page_generator_notification_message'},
    }
}

TRACKING_COOKIE_AGE = 30  # seconds: 30 seconds
TRACKING_COOKIE_DOMAIN = None  # No need to set specific domain for tests

RAVEN_CONFIG = {
    'dsn': 'https://be7092f5a43648119e03e77ec002caff:7739e5e90d1b4f1da99ef8db9ba1ca2b@app.getsentry.com/22626',
}
