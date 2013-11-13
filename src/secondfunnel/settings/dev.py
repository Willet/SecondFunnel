from .common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# CORS settings
# https://github.com/ottoyiu/django-cors-headers

CORS_ORIGIN_ALLOW_ALL = False

# File Storage
# http://django-storages.readthedocs.org/en/latest/

DEFAULT_FILE_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

STATICFILES_STORAGE = DEFAULT_FILE_STORAGE

AWS_STORAGE_BUCKET_NAME = 'secondfunnel-test-static'

# URLs for services:

INTENTRANK_BASE_URL = 'http://intentrank-test.elasticbeanstalk.com'

CONTENTGRAPH_BASE_URL = 'http://contentgraph-test.elasticbeanstalk.com/graph'