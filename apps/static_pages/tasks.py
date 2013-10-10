"""
Static pages celery tasks
"""

import json
from urlparse import urlparse

from celery import Celery, task, group
from celery.utils.log import get_task_logger

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache

from apps.assets.models import Store
from apps.contentgraph.views import get_page
from apps.intentrank.views import get_seeds_ir
from apps.pinpoint.models import Campaign
from apps.static_pages.models import StaticLog
from apps.utils import noop, proxy

from apps.static_pages.aws_utils import (create_bucket_website_alias,
    get_route53_change_status, upload_to_bucket)
from apps.static_pages.utils import (save_static_log, remove_static_log,
    bucket_exists_or_pending, get_bucket_name, create_dummy_request, render_campaign)

celery = Celery()
logger = get_task_logger(__name__)


ROUTE_53_LOCK_EXPIRE = 60 * 5
ROUTE_53_LOCK = "r53-lock"

ACQUIRE_LOCK = lambda: cache.add(
    ROUTE_53_LOCK, "true", ROUTE_53_LOCK_EXPIRE)
RELEASE_LOCK = lambda: cache.delete(ROUTE_53_LOCK)


def change_complete(store_id):
    try:
        store = Store.objects.get(id=store_id)

    except Store.DoesNotExist:
        logger.error("Store #{0} does not exist".format(store_id))
        return

    save_static_log(Store, store.id, "BU")
    remove_static_log(Store, store.id, "PE")

    RELEASE_LOCK()


@celery.task
def create_bucket_for_stores():
    stores = Store.objects.all()

    without_buckets = []
    for store in stores:
        if not bucket_exists_or_pending(store):
            without_buckets.append(store)

    task_group = group(create_bucket_for_store.s(s.id) for s in without_buckets)

    task_group.apply_async()


@celery.task
def create_bucket_for_store(store_id):
    if ACQUIRE_LOCK():
        try:
            store = Store.objects.get(id=store_id)

        except Store.DoesNotExist:
            logger.error("Store #{0} does not exist".format(store_id))
            return

        if bucket_exists_or_pending(store):
            return

        save_static_log(Store, store.id, "PE")

        store_url = ''
        if store.public_base_url:
            url = urlparse(store.public_base_url).hostname
            if url:
                store_url = url

        dns_name = get_bucket_name(store.slug)
        bucket_name =  store_url or dns_name
        _, change_status, change_id = create_bucket_website_alias(dns_name, bucket_name)

        if change_status == "PENDING":
            confirm_change_success.subtask((change_id, store_id)).delay()

        else:
            change_complete(store_id)

    # route53 is currently locked; try again in >5 seconds
    else:
        create_bucket_for_store.subtask((store_id,), countdown=5).delay()


@celery.task
def confirm_change_success(change_id, store_id):
    change_status = get_route53_change_status(change_id)

    if not change_status:
        logger.error("Change #{0} is missing. Can not verify its status."
        .format(
            change_id))
        return

    # change has not been applied yet
    if change_status == "PENDING":
        confirm_change_success.subtask(
            (change_id, store_id), countdown=5).delay()

    # change has been applied. Save that into log
    elif change_status == "INSYNC":
        change_complete(store_id)

    # not supposed to happen.
    # somehow Route53 API is returning an unknown change status
    else:
        logger.error("Route53: unknown status ({0}) for change #{1}".format(
            change_status, change_id))


@celery.task
def generate_static_campaigns():
    """Creates a group of tasks to generate/save campaigns,
    and runs them in parallel"""

    campaigns = Campaign.objects.all()

    task_group = group(generate_static_campaign.s(c.id)
        for c in campaigns)

    task_group.apply_async()


@celery.task
def generate_static_campaign(campaign_id, ignore_static_logs=False):
    """Renders individual campaign and saves it to S3.

    TODO: verify static log checks will be needed in the future, when the
    page generator is hosted on "barebones django app"
    """

    def create_campaign_from_dict(campaign_data):
        post_processing = proxy  # TODO: implement
        campaign_data = post_processing(campaign_data)
        return Campaign(campaign_data)

    try:
        campaign_json = get_page(store_id=None, page_id=campaign_id)

        # do -something- to turn ContentGraph JSON into a campaign object
        campaign = create_campaign_from_dict(campaign_json)

    except ValueError:  # json.loads exception
        logger.error("Could not understand campaign JSON #{0}".format(campaign_id))
        return

    dummy_request = create_dummy_request()

    # prepare the file name, static log, and the actual page
    s3_file_name = "index.html"
    log_key = "CD"
    page_content = render_campaign(campaign, get_seeds_func=get_seeds_ir,
                                   request=dummy_request)

    # if we think this static page already exists, finish task
    try:
        log_entry = StaticLog.objects.get(
            # content_type=content_type,
            content_type=None,
            object_id=campaign.id, key=log_key)

        if log_entry and ignore_static_logs:
            raise StaticLog.DoesNotExist('force-regeneration override')

    # otherwise, render and upload it
    except StaticLog.DoesNotExist:

        s3_path = "{0}/{1}".format(
            campaign.slug or campaign.id, s3_file_name)

        store_url = ''
        if campaign.store.public_base_url:
            url = urlparse(campaign.store.public_base_url).hostname
            if url:
                store_url = url

        dns_name = get_bucket_name(campaign.store.slug)
        bucket_name =  store_url or dns_name

        bytes_written = upload_to_bucket(
            bucket_name, s3_path, page_content, public=True)

        if bytes_written > 0:
            # remove any old entries
            remove_static_log(Campaign, campaign.id, log_key)

            # write a new log entry for this static campaign
            save_static_log(Campaign, campaign.id, log_key)

        # boto claims it didn't write anything to S3
        else:
            logger.error("Error uploading campaign #{0}: wrote 0 bytes".format(
                campaign_id))
