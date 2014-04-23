import os
import djcelery

from datetime import timedelta, datetime
import django.conf.global_settings as DEFAULT_SETTINGS

# default debug settings
DEBUG = False
TEMPLATE_DEBUG = DEBUG

DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'  # apparently something we need to enforce for File()

# aws environment specific settings
# These values should not be hardcoded. They are only hardcoded because
# it is convenient to do so :(
AWS_STORAGE_BUCKET_NAME = os.getenv('ProductionBucket', 'elasticbeanstalk-us-east-1-056265713214')
INTENTRANK_CONFIG_BUCKET_NAME = 'intentrank-config'
INTENTRANK_DEFAULT_NUM_RESULTS = 10
MEMCACHED_LOCATION = 'secondfunnel-cache.yz4kz2.cfg.usw2.cache.amazonaws.com:11211'
CLOUDFRONT_DOMAIN = 'cdn.secondfunnel.com'
CLOUDFRONT_USER_AGENT = 'Amazon CloudFront'

# Google analytics
GOOGLE_ANALYTICS_PROFILE = '67271131'         
GOOGLE_ANALYTICS_PROPERTY = 'UA-23764505-17' # dev and test (production has a separate profile, -16)  

ADMINS = (
    ('Nick "The Goat" Terwoord', 'nick@willetinc.com'),
    ('Brian "The Elite" Lai', 'brian@willetinc.com'),
    ('Kevin "The Awesome" Simpson', 'kevin@willetinc.com'),
    ('Alex "The Knight" Black', 'alexb@willetinc.com'),
    # ('Your Name', 'your_email@example.com'),
)

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'fraser@getwillet.com'
EMAIL_HOST_PASSWORD = 'w1llet!!'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

MANAGERS = ADMINS

BROWSER_CACHE_EXPIRATION_DATE = (datetime.now() + timedelta(minutes=30))\
    .strftime("%a, %d %b %Y %H:%M:%S GMT")

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

def from_project_root(path):
    """returns the path prepended by the project root."""
    return os.path.join(PROJECT_ROOT, path)

if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
            }
    }

    CONN_MAX_AGE = 0  # default to never time out from django's side;
                      # RDS is its own value set
else:  # defaults (dev) for letting bare django run -- do not modify
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
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

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

# "Storing static files as is" mode
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Cloudinary ImageService settings
CLOUDINARY_API_URL = "//api.cloudinary.com/v1_1/secondfunnel"
CLOUDINARY_BASE_URL = "//res.cloudinary.com/secondfunnel"
CLOUDINARY_NAME = "secondfunnel"
CLOUDINARY_API_KEY = "471718281466152"
CLOUDINARY_API_SECRET = "_CR94qpFu7EGChMbwmc4xqCsbXo"
CLOUDINARY = {
    'cloud_name': CLOUDINARY_NAME,
    'api_key': CLOUDINARY_API_KEY,
    'api_secret': CLOUDINARY_API_SECRET
}

# http://django_compressor.readthedocs.org/en/latest/remote-storages/
AWS_ACCESS_KEY_ID = 'AKIAJUDE7P2MMXMR55OQ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_SNS_REGION_NAME = 'us-west-2'
AWS_SQS_REGION_NAME = AWS_SNS_REGION_NAME  # by default, both oregon
AWS_SNS_TOPIC_NAME = 'page-generator'
AWS_SNS_LOGGING_TOPIC_NAME = 'page-generator-queue-log'
# allowed logging levels (arbitarily restricted)
AWS_SNS_LOGGING_LEVELS = ['info', 'warning', 'error']
AWS_SQS_QUEUE_NAME = AWS_SNS_TOPIC_NAME  # by default, same as the sns name

# dict of queues by region to poll regularly, using celery beat.
# corresponding handlers need to be imported in apps.api.tasks
AWS_SQS_POLLING_QUEUES = {
    # override in ./{environment}.py
}

# a (seemingly new) setting similar to SESSION_COOKIE_DOMAIN.
ALLOWED_HOSTS = '*'

# Disable signature/accesskey/expire attrs being appended to s3 links
AWS_QUERYSTRING_AUTH = False

COMPRESS_CSS_FILTERS = ['compressor.filters.css_default.CssAbsoluteFilter',
                        'compressor.filters.cssmin.CSSMinFilter']

COMPRESS_JS_FILTERS = ['compressor.filters.template.TemplateFilter',
                       'compressor.filters.jsmin.JSMinFilter']

# Rebuilds compressed files after 30 mins (in seconds)
COMPRESS_REBUILD_TIMEOUT = REBUILD_TIMEOUT = 30 * 60

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
    'raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # TODO: was last
    'django.middleware.gzip.GZipMiddleware',  # NOTE: Must be the first in this tuple
    'htmlmin.middleware.HtmlMinifyMiddleware',  # Enables compression of HTML
    'django.middleware.cache.CacheMiddleware',  # Manages caching
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Uncomment the next line for CSRF protection:
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    )

KEEP_COMMENTS_ON_MINIFYING = True

CACHE_MIDDLEWARE_SECONDS = 30 * 60  # Set the cache to at least 30 mins; will only affect production/test/demo

ROOT_URLCONF = 'secondfunnel.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'secondfunnel.wsgi.application'

TEMPLATE_DIRS = (
# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_admin_bootstrapped.bootstrap3', # before 'django_admin_bootstrapped'
    'django_admin_bootstrapped',  # before 'django.contrib.admin'
    'adminactions',  # before 'django.contrib.admin'
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',

    # external apps
    'djcelery',
    'storages',
    'south',
    'django_extensions',
    'tastypie',
    'rest_framework',
    'ajax_forms',
    'compressor',
    'corsheaders',
    'raven.contrib.django.raven_compat',  # logging

    # our apps
    'apps.api',
    'apps.assets',
    'apps.pinpoint',
    'apps.intentrank',
    'apps.contentgraph',
    'apps.website',
    'apps.static_pages',
    'apps.tracking',
    'apps.utils',
    'apps.imageservice',
    'apps.scraper',
)

CORS_ORIGIN_REGEX_WHITELIST = (
    # for testing local pages using live IR
    r'^(https?://)?(localhost|127.0.0.1):(\d+)$',
    r'^(https?://)?[\w-]+\.secondfunnel\.com$',
    r'^(https?://)?[\w-]+\.elasticbeanstalk\.com$',
    r'^(https?://)?[\w-]+\.myshopify\.com$',
    r'^(https?://)?[\w-]+\.amazonaws\.com$',
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
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['stderr', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
       },
    }
}

TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    # allows for request variable in templates
    'django.core.context_processors.request',
    # add custom context processors here
    'secondfunnel.context_processors.environment',
    'secondfunnel.context_processors.required_dimensions',
    'django.core.context_processors.request',
)

FIXTURE_DIRS = (
    'secondfunnel/fixtures/',
)

WEBSITE_BASE_URL = 'http://secondfunnel.com'
INTENTRANK_BASE_URL = WEBSITE_BASE_URL
CONTENTGRAPH_BASE_URL = 'http://contentgraph.elasticbeanstalk.com/graph'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

JENKINS_TASKS = (
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.run_pep8',
)

IMAGE_SERVICE_API = "http://imageservice.elasticbeanstalk.com"
IMAGE_SERVICE_STORE = "http://images.secondfunnel.com"
IMAGE_SERVICE_USER_AGENT = "Mozilla/5.0 (compatible; SecondFunnelBot/1.0; +http://secondfunnel.com/bot.hml)"
IMAGE_SERVICE_USER_AGENT_NAME = "SecondFunnelBot"
IMAGE_SERVICE_BUCKET = "images.secondfunnel.com"

STALE_TILE_QUEUE_NAME = 'tiles-worker-test-queue'

CELERYBEAT_POLL_INTERVAL = 60  # default beat is 60 seconds

CELERY_IMPORTS = ('apps.utils.tasks', )

API_LIMIT_PER_PAGE = 20

# only celery workers use this setting.
# run a celery worker with manage.py.
CELERYBEAT_SCHEDULE = {
    'poll 60-second queues': {
        'task': 'apps.api.tasks.poll_queues',
        'schedule': timedelta(seconds=CELERYBEAT_POLL_INTERVAL),
        'args': (CELERYBEAT_POLL_INTERVAL,)
    },
    'poll 5-second queues': {
        'task': 'apps.api.tasks.poll_queues',
        'schedule': timedelta(seconds=5),
        'args': (5,)
    },
    'poll 300-second queues': {
        'task': 'apps.api.tasks.poll_queues',
        'schedule': timedelta(seconds=300),
        'args': (300,)
    },
    'poll 60-second stale tiles': {
        'task': 'apps.api.tasks.queue_stale_tile_check',
        'schedule': timedelta(seconds=60),
        'args': tuple()
    },
    'poll 60-second regenerate pages': {
        'task': 'apps.api.tasks.queue_page_regeneration',
        'schedule': timedelta(seconds=300),
        'args': tuple()
    }
}

STALE_TILE_RETRY_THRESHOLD = 240  # seconds
IRCONFIG_RETRY_THRESHOLD = 240  # seconds

TASTYPIE_ALLOW_MISSING_SLASH = True  # allow missing trailing slashes

TRACKING_COOKIE_AGE = 60 * 60 * 24 * 30 # seconds: s*m*h*d; 30 days
TRACKING_COOKIE_DOMAIN = 'px.secondfunnel.com'

djcelery.setup_loader()
