"""
Django settings for secondfunnel project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z)9@rr6z8!fywx4%9vh&(7u%1u%n=$2!&+x80l%xoa*!&blv2k'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # External applications
    'tastypie',
    'corsheaders',
    'storages',

    # Our applications
    'apps.api',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
)

ROOT_URLCONF = 'secondfunnel.urls'

WSGI_APPLICATION = 'secondfunnel.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

# CORS settings
# https://github.com/ottoyiu/django-cors-headers

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

# File Storage
# http://django-storages.readthedocs.org/en/latest/backends/amazon-S3.html

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

STATICFILES_STORAGE = DEFAULT_FILE_STORAGE

# TODO: Should these be stored in the repo? Likely not...

AWS_ACCESS_KEY_ID = 'AKIAJUDE7P2MMXMR55OQ'

AWS_SECRET_ACCESS_KEY = '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'

AWS_STORAGE_BUCKET_NAME = os.getenv('ProductionBucket', 'elasticbeanstalk-us-east-1-056265713214')

# Disable signature/accesskey/expire attrs being appended to s3 links

AWS_QUERYSTRING_AUTH = False

# URLs for services:

INTENTRANK_BASE_URL = 'http://intentrank.elasticbeanstalk.com'

CONTENTGRAPH_BASE_URL = 'http://contentgraph.elasticbeanstalk.com/graph'

# TODO: Logging