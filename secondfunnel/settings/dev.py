from common import *

ENVIRONMENT = "dev"
DEBUG = True
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

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
        'ENGINE'  : 'django.db.backends.sqlite3',
        'NAME'    : 'dev.sqlite',
        'USER'    : '',
        'PASSWORD': '',
        'HOST'    : '',
        'PORT'    : '',
        }
}

'''  ( if you use MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ebdb',
        'USER': 'ebroot',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
'''

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            '127.0.0.1:11211',
        ]
    }
}

CONTENTGRAPH_BASE_URL = 'http://contentgraph-test.elasticbeanstalk.com/graph'

AWS_STORAGE_BUCKET_NAME = 'secondfunnel-test-static'

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
INTERNAL_IPS = ('127.0.0.1', INTERNAL_IP)
WEBSITE_BASE_URL = 'http://{0}:8000'.format(INTERNAL_IP)

STATIC_URL = '{0}/static/'.format(WEBSITE_BASE_URL)
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
