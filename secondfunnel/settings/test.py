from common import *
from secondfunnel.errors import EnvironmentSettingsError

if not all([AWS_STORAGE_BUCKET_NAME, MEMCACHED_LOCATION]):
    raise EnvironmentSettingsError()

DEBUG = True
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

COMPRESS_ENABLED = False

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
    "maintenancemode",
    "compressor",
    'social_auth',

    # our apps
    'apps.analytics',
    'apps.assets',
    'apps.pinpoint',
    'apps.website',
    'apps.scraper',
    'apps.static_pages',
)

WEBSITE_BASE_URL = 'http://secondfunnel-test.elasticbeanstalk.com'
AWS_STORAGE_BUCKET_NAME = 'secondfunnel-test-static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = 'https://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'
COMPRESS_URL = STATIC_URL

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

STATIC_CAMPAIGNS_BUCKET_NAME = 'campaigns-test.secondfunnel.com'

# Nick's test instagram client; good for secondfunnel-test
INSTAGRAM_CLIENT_ID = '3fc578b28e2a4b43a51ea2fa735599fd'
INSTAGRAM_CLIENT_SECRET = '1e12ec8c92304cd28582df05ab430762'

TUMBLR_CONSUMER_KEY = '0Y1uvESsK0gXkxfIFXfpU8OdlQN1QmMWenLo7ErDew3xDwtmcm'
TUMBLR_CONSUMER_SECRET = 'x2ElUhS9USOO57rqWZv8ElVYgAkaHoIbvTkExSR6vH5HeUnh5R'

GOOGLE_OAUTH2_CLIENT_ID = '218187505707-qj44j9dm83erjq9rukb5i4qvjd06q6pn.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = '1neVql1cfpEbP8XGhTM60Taa'