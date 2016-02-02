from common import *

ENVIRONMENT = "production"
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Enable GZIP and Minification
COMPRESS = True
COMPRESS_VERSION = True
COMPRESS_ENABLED = True
COMPRESS_CSS_HASHING_METHOD = 'content'

AWS_IS_GZIPPED = True # GZip Middleware isn't recognized without this line because http://stackoverflow.com/a/19180415/1558430
AWS_S3_CUSTOM_DOMAIN = CLOUDFRONT_DOMAIN
AWS_S3_SECURE_URLS = False
AWS_HEADERS = {
    'Expires': BROWSER_CACHE_EXPIRATION_DATE,
    'Cache-Control': "public, max-age=1800",
    'Vary': 'Accept-Encoding',
}

WEBSITE_BASE_URL = 'http://tng-master.secondfunnel.com'
INTENTRANK_BASE_URL = WEBSITE_BASE_URL
AWS_STORAGE_BUCKET_NAME = os.getenv('TestBucket', 'elasticbeanstalk-us-east-1-056265713214')
INTENTRANK_CONFIG_BUCKET_NAME = 'intentrank-config-test'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'.format(WEBSITE_BASE_URL)

# django compressor uses COMPRESS_URL as static file prefices
COMPRESS_URL = 'http://%s/' % CLOUDFRONT_DOMAIN

# or '.elasticbeanstalk.com'
SESSION_COOKIE_DOMAIN = '.secondfunnel.com'

STALE_TILE_QUEUE_NAME = 'tileservice-worker-queue'

MEMCACHED_LOCATION = 'secondfunnel-cache.yz4kz2.cfg.usw2.cache.amazonaws.com:11211'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': MEMCACHED_LOCATION
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

GOOGLE_SERVICE_ACCOUNT = '248578306350@developer.gserviceaccount.com'

BROKER_URL = 'sqs://%s:%s@' % (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
BROKER_TRANSPORT_OPTIONS = {
    'region': 'us-west-2',
    'visibility_timeout': 3600,  # 1 hour. (Possible fix for recurring tasks issue on SQS)
    'polling_interval': 1,
    'queue_name_prefix': 'celery-',
}

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
    }
}

RAVEN_CONFIG = {
    'dsn': 'http://be7092f5a43648119e03e77ec002caff:7739e5e90d1b4f1da99ef8db9ba1ca2b@app.getsentry.com/22626',
}

KEEN_CONFIG = {
    'projectId': '5356c34836bf5a7d68000001',
    'writeKey': '7c6e9f9f3d669595dc2db03c4fedc5a71f8f2693f9847693cc49ba97857c256d9b90ac79bd849b153174aa39ed67f18780e9abb525e69c2e01ba4eb397a25286f45dec5001f081949a0029d676c7aa37924c6add8a5abbf6e90a279d42c15b3847ddd1750d282d5e93769b97169e8de9',
    'readKey': '0cfb3f08011f93aa29e992471f6ae9e5f9e2397045d59dfb07d0663c40ddd63f6300f782d000b0fd24f5776c04d0f22d5d321d90ee57a8e9a120d553527eea0e8aa005344338a1710432ef48174d84acbb84bcb6813701a1d3769dc6adb333a0418ac1e6784cb16c3df55a4a4477235d'
}

PREDICTION_IO_API_KEY = "CuBN5rs075a1WfQLy3gyPbWpmBIrHOQ9zQbufFwmSuNPwYf2npznXncLw2j2vTlL"

# Add Raven Middleware (getsentry.com)
MIDDLEWARE_CLASSES = ('raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',) + MIDDLEWARE_CLASSES

THIRD_PARTY_APPS += ('raven.contrib.django.raven_compat',)  # logging
INSTALLED_APPS = FRAMEWORK_APPS + THIRD_PARTY_APPS + LOCAL_APPS
