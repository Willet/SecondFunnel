from common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

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
