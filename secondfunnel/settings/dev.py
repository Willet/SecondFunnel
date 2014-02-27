from common import *

ENVIRONMENT = "dev"
DEBUG = True
TEMPLATE_DEBUG = DEBUG

def internal_ip():
    """INTERNAL! TESTING ONLY!

    http://stackoverflow.com/a/166589/1558430
    """
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("google.com", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'sfdb',
        'USER': 'sf',
        'PASSWORD': 'postgres',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            '127.0.0.1:11211',
        ]
    }
}

INSTALLED_APPS += (
    'django_nose',  # for testing...? we don't use it, but here it is
)

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
        # https://willet.atlassian.net/browse/CM-125
        'product-update-notification-queue-dev':
            {'queue_name': 'product-update-notification-queue-dev',
             'handler': 'handle_product_update_notification_message',
             'interval': 300},

        # https://willet.atlassian.net/browse/CM-126
        'content-update-notification-queue-dev':
            {'queue_name': 'content-update-notification-queue-dev',
             'handler': 'handle_content_update_notification_message',
             'interval': 300},

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

CONTENTGRAPH_BASE_URL = 'http://contentgraph-test.elasticbeanstalk.com/graph'

CORS_ORIGIN_REGEX_WHITELIST = (
    '^(localhost|127.0.0.1):(\d+)$'
)

AWS_STORAGE_BUCKET_NAME = 'secondfunnel-test-static'
# copy value from test to enable dev box transfers

INTENTRANK_CONFIG_BUCKET_NAME = None
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# We should be able to just run `bundle exec sass` in dev as we do in
# production. Until we've figured that out, just running things this way
COMPRESS_PRECOMPILERS = (
    ('text/x-sass', 'sass {infile} {outfile}'),
    ('text/x-scss', 'sass {infile} {outfile}'),
)

DEFAULT_FILE_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
COMPRESS_STORAGE = STATICFILES_STORAGE

INTERNAL_IP = internal_ip()
INTERNAL_IPS = ('127.0.0.1', # virtualenv
                'localhost',
                '10.0.1.1',  # vagrant
                '10.0.2.2',
                '24.137.221.230',  # waterloo office
                '10.217.146.216',  # the elastic load balancer (I think)
                INTERNAL_IP)

WEBSITE_BASE_URL = ''.format(INTERNAL_IP)
#WEBSITE_BASE_URL = 'http://{0}:8000'.format(INTERNAL_IP)
INTENTRANK_BASE_URL = WEBSITE_BASE_URL

STATIC_URL = '/static/'.format(WEBSITE_BASE_URL)
COMPRESS_URL = STATIC_URL
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

GOOGLE_ANALYTICS_PROFILE = '67271131'
GOOGLE_ANALYTICS_PROPERTY = 'UA-23764505-15'

GOOGLE_API_PRIVATE_KEY = 'google-service-account-prod.p12'  # (a file)
GOOGLE_SERVICE_ACCOUNT = '248578306350@developer.gserviceaccount.com'

BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# Social Auth
# Nick's test instagram client; good for localhost:8000
INSTAGRAM_CLIENT_ID = '1410bbbf8b614ebfb77081d5293cf48d'
INSTAGRAM_CLIENT_SECRET = 'c535ee3141944cdbaab97954b6b85083'

GOOGLE_OAUTH2_CLIENT_ID = '218187505707.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = 'yb7YyXBSzn0hq5f-tHdcKEQU'

TUMBLR_CONSUMER_KEY = 'iKb1SAF5JwVnhLPSv7R7sqTYYekvkYOmmyYIRV8anFiT1xx2lD'
TUMBLR_CONSUMER_SECRET = 'qIiqecbZeR3LSLjGcuzmkkkgAmYFrpd3ilSDHkNe5HksZHKInH'

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
SHOW_TOOLBAR_CALLBACK = lambda: True

# Monkeypatch decorator care of Van Rossum himself!
# http://mail.python.org/pipermail/python-dev/2008-January/076194.html
def monkeypatch_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

# Fix for SQLite DBs and potential migration problems
# https://groups.google.com/forum/#!msg/south-users/y0ZYm6hSeWc/by7d8GwuN68J
from south.db.sqlite3 import DatabaseOperations

@monkeypatch_method(DatabaseOperations)
def _get_full_table_description(self, connection, cursor, table_name):
    cursor.execute('PRAGMA table_info(%s)' % connection.ops.quote_name(table_name))
    # cid, name, type, notnull, dflt_value, pk

    def _normalize(field):
        if field is not None:
            field = field.replace('%', '%%')
        return field

    return [{'name': field[1],
             'type': field[2],
             'null_ok': not field[3],
             'dflt_value': _normalize(field[4]),
             'pk': field[5]     # undocumented
            } for field in cursor.fetchall()]
