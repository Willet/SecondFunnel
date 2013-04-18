from common import *
from secondfunnel.errors import EnvironmentSettingsError

if not all([AWS_STORAGE_BUCKET_NAME, MEMCACHED_LOCATION]):
    raise EnvironmentSettingsError()

DEBUG = False
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

COMPRESS_ENABLED = True

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
    'maintenancemode',
    'compressor',
    'social_auth',

    # our apps
    'apps.analytics',
    'apps.assets',
    'apps.pinpoint',
    'apps.website',
    'apps.scraper',
    'apps.static_pages',
)

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
    'queue_name_prefix': 'celery-',
}
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

INSTAGRAM_CLIENT_ID = 'be95027932f64f4aaa465ffed160a8fb'
INSTAGRAM_CLIENT_SECRET = 'aac059c1acb341d3b44b9139dc106dbe'

TUMBLR_CONSUMER_KEY = 'Kr9rF0bykYZ2J2ncURUkwG0BBAEaDy7VGGzWZnVjna0bKPbRTn'
TUMBLR_CONSUMER_SECRET = 'aLK2zeDeTbITx03iFSPntIBRV9EIel6pl2Sp9ARbyMIEykGHXF'

GOOGLE_OAUTH2_CLIENT_ID = '218187505707-usif3u64gdr68rposjubk4461elk1e5c.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = 'O_C-_zo1dXQQkg989-LwJNbt'
