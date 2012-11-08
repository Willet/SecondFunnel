import os

# Debugging settings
DEBUG          = True
TEMPLATE_DEBUG = DEBUG
MEDIA_DEV_MODE = DEBUG  # django-mediagenerator

# Installed applications
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
    'storages',
    'south',
    'django_extensions',
    'tastypie',
    'mediagenerator',
    'ajax_forms',

    # our apps
    'apps.analytics',
    'apps.assets',
    'apps.pinpoint',
    'apps.website',
    'apps.scraper',
)

# Middleware
MIDDLEWARE_CLASSES = (
    # Media middleware has to come first
    'mediagenerator.middleware.MediaMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Templates
TEMPLATE_DIRS    = ()
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#    'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # allows for request variable in templates
    'django.core.context_processors.request',

    # needed for admin
    'django.contrib.auth.context_processors.auth',

    # allows for the django messages framework
    'django.contrib.messages.context_processors.messages',
)

# AWS Settings
AWS_ACCESS_KEY_ID       = 'AKIAJUDE7P2MMXMR55OQ'
AWS_SECRET_ACCESS_KEY   = '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'
AWS_STORAGE_BUCKET_NAME = 'elasticbeanstalk-us-east-1-056265713214'

# Static files and uploads
MEDIA_ROOT           = ''
MEDIA_URL            = ''
STATIC_URL           = '/static/'
DEV_MEDIA_URL        = '/devmedia/'  # django-mediagenerator
PRODUCTION_MEDIA_URL = 'http://{bucket}.s3.amazonaws.com/'.format(bucket=AWS_STORAGE_BUCKET_NAME) #  django-mediagenerator

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATIC_ROOT = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))), 'static')

STATICFILES_DIRS = (
    os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__))), 'secondfunnel/_generated_media'),
)
GLOBAL_MEDIA_DIRS = STATICFILES_DIRS  # django-mediagenerator

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE  = 'storages.backends.s3boto.S3BotoStorage'

ROOT_MEDIA_FILTERS = {  # django-mediagenerator
#    'js' : 'mediagenerator.filters.closure.Closure', # Supports Google Closure compiler
#    'css': 'mediagenerator.filters.yuicompressor.YUICompressor',  # ...And YUI Compressor
}

#YUICOMPRESSOR_PATH    = '/path/to/yuicompressor'
#CLOSURE_COMPILER_PATH = '/path/to/closure/compiler'


SASS_FRAMEWORKS = ()  # http://www.allbuttonspressed.com/projects/django-mediagenerator#id23

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Database settings
if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }

FIXTURE_DIRS = (
    'secondfunnel/fixtures/',
)

# Internationalization / Localization
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'America/Chicago'
USE_TZ        = True
USE_I18N      = True
USE_L10N      = True

# Miscellaneous
SECRET_KEY       = '44$s)fsfz#liv*o3^ax82m!9jh1!%lmg&amp;)@1b5z+m*)uhrn4=l'
SITE_ID          = 1
WSGI_APPLICATION = 'secondfunnel.wsgi.application'
ROOT_URLCONF     = 'secondfunnel.urls'

ADMINS   = (
#    ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

# Media bundles
MEDIA_BUNDLES = (  # django-mediagenerator
# Combine files (can combine either js or css files)
#   ('filename.js',
#       'file1.js',
#       'file2.js'),
# Combine files (recognizes .coffee, .scss, .sass)
#   ('filename2.js',
#       'my.coffee'),
#   ('sassy.css',
#       'sass.scss',
#       'scss.sass'),
# Combine files (even in dev mode)
#   ('combined.js',
#       'file1.js',
#       {
#           'filter': 'mediagenerator.filters.concat.Concat',
#           'dev_output_name': 'test.js'
#           'concat_dev_output': True,
#           'input': ('file2.js', 'file3.js')
#       }),
)

# Include local settings
try:
    from local_settings import *
except ImportError, e:
    pass
