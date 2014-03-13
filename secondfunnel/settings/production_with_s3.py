import os
from secondfunnel.errors import EnvironmentSettingsError
from common import BROWSER_CACHE_EXPIRATION_DATE, MEMCACHED_LOCATION

AWS_STORAGE_BUCKET_NAME = os.getenv('ProductionBucket', 'elasticbeanstalk-us-east-1-056265713214')

if not all([AWS_STORAGE_BUCKET_NAME, MEMCACHED_LOCATION]):
    raise EnvironmentSettingsError()

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = DEFAULT_FILE_STORAGE
STATIC_URL = 'http://' + AWS_STORAGE_BUCKET_NAME + '.s3.amazonaws.com/'

