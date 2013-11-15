import json
from urlparse import urlparse
from django.conf import settings
from django.core.cache import cache
from apps.contentgraph.views import proxy_store
from apps.utils.s3 import create_bucket_website_alias, get_bucket_name

ROUTE_53_LOCK_EXPIRE = 60 * 5
ROUTE_53_LOCK = "r53-lock"

ACQUIRE_LOCK = lambda: cache.add(
    ROUTE_53_LOCK, "true", ROUTE_53_LOCK_EXPIRE)
RELEASE_LOCK = lambda: cache.delete(ROUTE_53_LOCK)

def get_or_create_bucket(store_id):
    ACQUIRE_LOCK()

    store_json, _ = proxy_store(store_id, raw=True)
    store = json.loads(store_json)

    store_url = ''
    if store.get('public-base-url', False):
        url = urlparse(store.get('public-base-url')).hostname
        if url:
            store_url = url

    dns_name = get_bucket_name(store.get('slug'))
    bucket_name = store_url or dns_name

    # check for dev/test prefix. This allows campaign.url from campaign manager
    # to be a full secondfunnel.com url.
    if settings.ENVIRONMENT in ["test", "dev"]:
        if not bucket_name[:len(settings.ENVIRONMENT)] == settings.ENVIRONMENT:
            bucket_name = '{0}-{1}'.format(settings.ENVIRONMENT, bucket_name)

    _, change_status, change_id = create_bucket_website_alias(dns_name, bucket_name)

    RELEASE_LOCK()