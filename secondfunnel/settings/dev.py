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

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

GOOGLE_ANALYTICS_PROFILE = '63888985'
GOOGLE_ANALYTICS_PROPERTY = 'UA-34721035-1'

BROKER_URL = 'amqp://guest:guest@localhost:5672//'
