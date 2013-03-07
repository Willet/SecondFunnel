import os
import djcelery

from datetime import timedelta
import django.conf.global_settings as DEFAULT_SETTINGS

# Django settings for secondfunnel project.
import sys

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# aws environment specific settings
# These values should not be hardcoded. They are only hardcoded because
# We have not yet found a way to set environment variables :(
AWS_STORAGE_BUCKET_NAME = os.getenv('ProductionBucket', 'elasticbeanstalk-us-east-1-056265713214')
MEMCACHED_LOCATION = 'secondfunnel-cache.yz4kz2.cfg.usw2.cache.amazonaws.com:11211'

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS


def fromProjectRoot(path):
    return os.path.join(
           os.path.dirname(
           os.path.dirname(
           os.path.dirname(
           os.path.abspath(__file__)))), path)

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
else:
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

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

LOCALE_PATHS = (
    fromProjectRoot('locale'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"

# TODO: has to be a better way to get the path...
STATIC_ROOT = fromProjectRoot('static')

DEFAULT_FILE_STORAGE = 'secondfunnel.storage.CustomExpiresS3BotoStorage'
STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
# http://django_compressor.readthedocs.org/en/latest/remote-storages/
AWS_ACCESS_KEY_ID = 'AKIAJUDE7P2MMXMR55OQ'
AWS_SECRET_ACCESS_KEY = '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'

STATIC_ASSET_TIMEOUT = 1209600  # two weeks

AWS_EXPIRES_REGEXES = [
    ('^CACHE/', STATIC_ASSET_TIMEOUT),
]

COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter',
                        'compressor.filters.cssmin.CSSMinFilter']

COMPRESS_STORAGE = STATICFILES_STORAGE

COMPRESS_PRECOMPILERS = (
    ('text/x-sass', 'bundle exec sass {infile} {outfile}'),
    ('text/x-scss', 'bundle exec sass {infile} {outfile}'),
)

COMPRESS_PARSER = 'compressor.parser.LxmlParser'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)))), 'secondfunnel/static'),
    )

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'compressor.finders.CompressorFinder',
    )

# Make this unique, and don't share it with anybody.
SECRET_KEY = '44$s)fsfz#liv*o3^ax82m!9jh1!%lmg&amp;)@1b5z+m*)uhrn4=l'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
    )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    )

ROOT_URLCONF = 'secondfunnel.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'secondfunnel.wsgi.application'

TEMPLATE_DIRS = (
# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
)

LETTUCE_APPS = (
    'apps.pinpoint',
)

LETTUCE_AVOID_APPS = (
)

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
    'django_nose', # Must be included after 'south'
    'lettuce.django',
    'adminlettuce',
    'ajax_forms',
    "compressor",
    "maintenancemode",
    'social_auth',

    # our apps
    'apps.analytics',
    'apps.assets',
    'apps.pinpoint',
    'apps.website',
    'apps.scraper',

    # CI
    'django_jenkins',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
JENKINS_TEST_RUNNER = 'django_jenkins.nose_runner.CINoseTestSuiteRunner'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
     'version': 1,
     'disable_existing_loggers': False,
     'formatters': {
         'verbose': {
             'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
         },
         'simple': {
             'format': '%(levelname)s %(message)s'
         },
     },
     'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse'
         }
     },
     'handlers': {
         'stderr': {
             'level': 'ERROR',
             'class': 'logging.StreamHandler',
             'formatter': 'verbose'
         },
         'mail_admins': {
             'level': 'ERROR',
             'filters': ['require_debug_false'],
             'class': 'django.utils.log.AdminEmailHandler'
         }
     },
     'loggers': {
         'django.request': {
             'handlers': ['stderr', 'mail_admins'],
             'level': 'ERROR',
             'propagate': True,
         },
     }
}

TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    # allows for request variable in templates
    'django.core.context_processors.request',

    # allows for external settings dict
    'secondfunnel.context_processors.expose_settings',

    # needed for admin
    'django.contrib.auth.context_processors.auth',

    # allows for the django messages framework
    'django.contrib.messages.context_processors.messages',

    # used for internationalization
    'django.core.context_processors.i18n',
    )

FIXTURE_DIRS = (
    'secondfunnel/fixtures/',
)

EXPOSED_SETTINGS = {
    'STATIC_ASSET_TIMEOUT': STATIC_ASSET_TIMEOUT
}

WEBSITE_BASE_URL = 'http://www.secondfunnel.com'
INTENTRANK_BASE_URL = 'http://intentrank.elasticbeanstalk.com'

CELERYBEAT_SCHEDULE = {
    'runs-every-6-hours': {
        'task': 'apps.analytics.tasks.redo_analytics',
        'schedule': timedelta(hours=6),
    },
}

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.contrib.instagram.InstagramBackend',
    'django.contrib.auth.backends.ModelBackend',
)
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = '/pinpoint/admin/social-auth/'

MAINTENANCE_IGNORE_URLS = (r'^/$',
                           r'^/about/?$',
                           r'^/contact/?$',
                           r'^/static/?',
                           r'^/why/?$', )

JENKINS_TASKS = (
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.with_coverage',
)

djcelery.setup_loader()
