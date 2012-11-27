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
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'secondfunnel'
    }
}

DEFAULT_FILE_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
COMPRESS_STORAGE = STATICFILES_STORAGE
COMPRESS_ENABLED = True

STATIC_URL = '/static/'
COMPRESS_URL = STATIC_URL
