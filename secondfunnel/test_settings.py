DATABASES = {
 'default': {
  'ENGINE': 'django.db.backends.sqlite3',
  'NAME': 'db.db',
  'USER': '',
  'PASSWORD': '',
  'HOST': '',
  'PORT': '',
 }
}

MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_URL = '/static/'
TEMPLATE_DIRS = ()
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

EMAIL_HOST = '127.0.0.1'
EMAIL_PORT = '1025'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

BROKER_URL = 'amqp://guest:guest@localhost:5672//'
BROKER_TRANSPORT_OPTIONS = {
    'region': 'eu-west-1',
    'visibility_timeout': 30,
    'polling_interval': 1,
    'queue_name_prefix': 'celery-',
}
