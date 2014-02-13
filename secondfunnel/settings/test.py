from common import *
from secondfunnel.errors import EnvironmentSettingsError

if not all([AWS_STORAGE_BUCKET_NAME, MEMCACHED_LOCATION]):
    raise EnvironmentSettingsError()

ENVIRONMENT = "test"
DEBUG = False
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

# Enable GZIP and Minification
COMPRESS = True
COMPRESS_VERSION = True
COMPRESS_ENABLED = True

AWS_IS_GZIPPED = True # GZip Middleware isn't recognized without this line because http://stackoverflow.com/a/19180415/1558430
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
    "compressor",
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
    'apps.utils'
)

WEBSITE_BASE_URL = 'http://test.secondfunnel.com'
INTENTRANK_BASE_URL = 'http://intentrank-test.elasticbeanstalk.com'
CONTENTGRAPH_BASE_URL = 'http://contentgraph-test.elasticbeanstalk.com/graph'
AWS_STORAGE_BUCKET_NAME = os.getenv('TestBucket', 'elasticbeanstalk-us-east-1-056265713214')
INTENTRANK_CONFIG_BUCKET_NAME = 'intentrank-config-test'

# if secondfunnel-test.elasticbeanstalk.com
# SESSION_COOKIE_DOMAIN = '.elasticbeanstalk.com'
# if test.secondfunnel.com (recommended)
SESSION_COOKIE_DOMAIN = '.secondfunnel.com'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
COMPRESS_URL = STATIC_URL

MEMCACHED_LOCATION = 'secondfunnel-test.yz4kz2.cfg.usw2.cache.amazonaws.com:11211'

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
    'visibility_timeout': 30,
    'polling_interval': 1,
    'queue_name_prefix': 'celery-test-',
    }

# Nick's test instagram client; good for secondfunnel-test
INSTAGRAM_CLIENT_ID = '3fc578b28e2a4b43a51ea2fa735599fd'
INSTAGRAM_CLIENT_SECRET = '1e12ec8c92304cd28582df05ab430762'

TUMBLR_CONSUMER_KEY = '0Y1uvESsK0gXkxfIFXfpU8OdlQN1QmMWenLo7ErDew3xDwtmcm'
TUMBLR_CONSUMER_SECRET = 'x2ElUhS9USOO57rqWZv8ElVYgAkaHoIbvTkExSR6vH5HeUnh5R'

GOOGLE_OAUTH2_CLIENT_ID = '218187505707-qj44j9dm83erjq9rukb5i4qvjd06q6pn.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = '1neVql1cfpEbP8XGhTM60Taa'
