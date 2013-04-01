# Apparently, it is not possible to import two levels deep in Django?
# Copied from `dev.py`

from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            '127.0.0.1:11211',
            ]
    }
}

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
COMPRESS_ENABLED = False

STATIC_URL = '/static/'
COMPRESS_URL = STATIC_URL
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

GOOGLE_ANALYTICS_PROFILE = '63888985'
GOOGLE_ANALYTICS_PROPERTY = 'UA-34721035-1'

GOOGLE_API_PRIVATE_KEY = 'google-service-account-prod.p12'
GOOGLE_SERVICE_ACCOUNT = '248578306350@developer.gserviceaccount.com'

BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# Nick's test instagram client; good for localhost:8000
INSTAGRAM_CLIENT_ID = '1410bbbf8b614ebfb77081d5293cf48d'
INSTAGRAM_CLIENT_SECRET = 'c535ee3141944cdbaab97954b6b85083'

STATIC_CAMPAIGNS_BUCKET_NAME = 'campaigns-test.secondfunnel.com'

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