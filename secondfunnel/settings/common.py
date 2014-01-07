import os
import djcelery

from datetime import timedelta, datetime
import django.conf.global_settings as DEFAULT_SETTINGS

# Django settings for secondfunnel project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG
MOCK_IR_SERVER = False

DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'  # apparently something we need to enforce for File()

# aws environment specific settings
# These values should not be hardcoded. They are only hardcoded because
# We have not yet found a way to set environment variables :(
AWS_STORAGE_BUCKET_NAME = os.getenv('ProductionBucket', 'elasticbeanstalk-us-east-1-056265713214')
MEMCACHED_LOCATION = 'secondfunnel-cache.yz4kz2.cfg.usw2.cache.amazonaws.com:11211'

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

BROWSER_CACHE_EXPIRATION_DATE = (datetime.now() + timedelta(days=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")

def from_project_root(path):
    """returns the path prepended by the project root."""
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
    from_project_root('locale'),
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
MIN_MEDIA_WIDTH = 480
MIN_MEDIA_HEIGHT = 1

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"

# TODO: has to be a better way to get the path...
STATIC_ROOT = from_project_root('static')

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
# http://django_compressor.readthedocs.org/en/latest/remote-storages/
AWS_ACCESS_KEY_ID = 'AKIAJUDE7P2MMXMR55OQ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_SNS_REGION_NAME = 'us-west-2'
AWS_SQS_REGION_NAME = AWS_SNS_REGION_NAME  # by default, both oregon
AWS_SNS_TOPIC_NAME = 'page_generator'
AWS_SQS_QUEUE_NAME = AWS_SNS_TOPIC_NAME  # by default, same as the sns name

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
AWS_SQS_POLLING_QUEUES = {
    'us-west-2': {
        # https://willet.atlassian.net/browse/CM-125
        'product-update-notification-queue':
            {'queue_name': 'product-update-notification-queue',
             'handler': 'handle_product_update_notification_message',
             'interval': 300},

        # https://willet.atlassian.net/browse/CM-126
        'content-update-notification-queue':
            {'queue_name': 'content-update-notification-queue',
             'handler': 'handle_content_update_notification_message',
             'interval': 300},

        # https://willet.atlassian.net/browse/CM-127
        'tile-generator-notification-queue':
            {'queue_name': 'tile-generator-notification-queue',
             'handler': 'handle_tile_generator_update_notification_message'},

        # https://willet.atlassian.net/browse/CM-128
        'ir-config-generator-notification-queue':
            {'queue_name': 'ir-config-generator-notification-queue',
             'handler': 'handle_ir_config_update_notification_message'},

        # https://willet.atlassian.net/browse/CM-124
        'scraper-notification-queue':
            {'queue_name': 'scraper-notification-queue',
             'handler': 'handle_scraper_notification_message'},

        'page_generator':
            {'queue_name': 'page_generator',
             'handler': 'handle_page_generator_notification_message'},
    }
}

# Disable signature/accesskey/expire attrs being appended to s3 links
AWS_QUERYSTRING_AUTH = False

COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter',
                        'compressor.filters.cssmin.CSSMinFilter']

COMPRESS_JS_FILTERS = ['compressor.filters.template.TemplateFilter',
                       'compressor.filters.jsmin.JSMinFilter']
                       
COMPRESS_REBUILD_TIMEOUT = 2592000 # Rebuilds compressed files after 30 days (in seconds)

COMPRESS_STORAGE = STATICFILES_STORAGE

COMPRESS_PRECOMPILERS = (
    ('text/x-sass', 'bundle exec sass {infile} {outfile}'),
    ('text/x-scss', 'bundle exec sass {infile} {outfile}'),
)

COMPRESS_PARSER = 'compressor.parser.LxmlParser'

# When GZIP is enabled, these types will be GZIPPED
GZIP_CONTENT_TYPES = (
    'text/plain',
    'text/html',
    'text/xml',
    'text/css',
    'text/javascript',
    'application/xml',
    'application/xhtml+xml',
    'application/rss+xml',
    'application/javascript',
    'application/x-javascript',
)
    

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
    'django.middleware.gzip.GZipMiddleware', # NOTE: Must be the first in this tuple
    'htmlmin.middleware.HtmlMinifyMiddleware', # Enables compression of HTML
    'django.middleware.cache.CacheMiddleware', # Manages caching
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    )

KEEP_COMMENTS_ON_MINIFYING = True

CACHE_MIDDLEWARE_SECONDS = 604800 # Set the cache to atleast a week; will only affect production/test/demo

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
    'compressor',
    'maintenancemode',
    'social_auth',
    'corsheaders',

    # our apps
    'apps.api',
    'apps.assets',
    'apps.pinpoint',
    'apps.intentrank',
    'apps.contentgraph',
    'apps.website',
    'apps.static_pages',
    'apps.utils',
)

CORS_ORIGIN_REGEX_WHITELIST = (
    '^[\w-]+\.secondfunnel\.com$'
)
CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'ApiKey'
)
CORS_ALLOW_CREDENTIALS = True

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
JENKINS_TEST_RUNNER = 'django_jenkins.nose_runner.CINoseTestSuiteRunner'
COVERAGE_REPORT_HTML_OUTPUT_DIR = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)))), 'test_report')

COVERAGE_ADDITIONAL_MODULES = ['apps']
COVERAGE_PATH_EXCLUDES = ['.env', 'migrations']

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
    # add custom context processors here
    'secondfunnel.context_processors.environment',
    'secondfunnel.context_processors.required_dimensions',
)

FIXTURE_DIRS = (
    'secondfunnel/fixtures/',
)

WEBSITE_BASE_URL = 'http://www.secondfunnel.com'
INTENTRANK_BASE_URL = 'http://intentrank.elasticbeanstalk.com'
CONTENTGRAPH_BASE_URL = 'http://contentgraph.elasticbeanstalk.com/graph'

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.contrib.instagram.InstagramBackend',
    'social_auth.backends.google.GoogleOAuth2Backend',
    'social_auth.backends.contrib.tumblr.TumblrBackend',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social_auth.backends.pipeline.social.social_auth_user',
    'social_auth.backends.pipeline.social.associate_user',
    'social_auth.backends.pipeline.social.load_extra_data',
    'social_auth.backends.pipeline.user.update_user_details',
    'apps.utils.social.utils.update_social_auth'
)

SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = \
    '/pinpoint/admin/social-auth/connect/'
SOCIAL_AUTH_DISCONNECT_REDIRECT_URL = \
    '/pinpoint/admin/social-auth/disconnect/'

INSTAGRAM_AUTH_EXTRA_ARGUMENTS = {'scope': 'likes'}
GOOGLE_OAUTH_EXTRA_SCOPE = ['https://gdata.youtube.com']

GOOGLE_OAUTH2_EXTRA_DATA = [('email', 'username')]

MAINTENANCE_IGNORE_URLS = (r'^/$',
                           r'^/about/?$',
                           r'^/contact/?$',
                           r'^/static/?',
                           r'^/why/?$', )

JENKINS_TASKS = (
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.run_pep8',
)

IMAGE_SERVICE_API = "http://imageservice.elasticbeanstalk.com"
IMAGE_SERVICE_STORE = "http://images.secondfunnel.com"

STALE_TILE_QUEUE_NAME = 'tiles-worker-test-queue'

CELERYBEAT_POLL_INTERVAL = 60  # default beat is 60 seconds

# only celery workers use this setting.
# run a celery worker with manage.py.
CELERYBEAT_SCHEDULE = {
    'poll 60-second queues': {
        'task': 'apps.api.tasks.poll_queues',
        'schedule': timedelta(seconds=CELERYBEAT_POLL_INTERVAL),
        'args': (CELERYBEAT_POLL_INTERVAL)
    },
    'poll 300-second queues': {
        'task': 'apps.api.tasks.poll_queues',
        'schedule': timedelta(seconds=300),
        'args': (300)
    },
    'poll 60-second stale tiles': {
        'task': 'apps.api.tasks.queue_stale_tile_check',
        'schedule': timedelta(seconds=60),
    }
}

djcelery.setup_loader()
