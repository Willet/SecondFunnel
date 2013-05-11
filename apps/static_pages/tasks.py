"""
Static pages celery tasks
"""

from celery import task, group
from celery.utils.log import get_task_logger

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache

from apps.assets.models import Store
from apps.pinpoint.models import Campaign
from apps.pinpoint.utils import render_campaign
from apps.static_pages.models import StaticLog

from apps.static_pages.aws_utils import (create_bucket_website_alias,
    get_route53_change_status, upload_to_bucket)
from apps.static_pages.utils import (save_static_log, remove_static_log,
    bucket_exists_or_pending, get_bucket_name)

# TODO: make use of logging, instead of suppressing errors as is done now
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


@task()
def create_bucket_for_stores():
    stores = Store.objects.all()

    without_buckets = []
    for store in stores:
        if not bucket_exists_or_pending(store):
            without_buckets.append(store)

    task_group = group(create_bucket_for_store.s(s.id) for s in without_buckets)

    task_group.apply_async()


@task()
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

        _, change_status, change_id = create_bucket_website_alias(
            get_bucket_name(store.slug))

        if change_status == "PENDING":
            confirm_change_success.subtask((change_id, store_id)).delay()

        else:
            change_complete(store_id)

    # route53 is currently locked; try again in >5 seconds
    else:
        create_bucket_for_store.subtask((store_id,), countdown=5).delay()


@task()
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


@task()
def generate_static_campaigns():
    """Creates a group of tasks to generate/save campaigns,
    and runs them in parallel"""

    campaigns = Campaign.objects.all()

    task_group = group(generate_static_campaign.s(c.id)
        for c in campaigns)

    task_group.apply_async()


@task()
def generate_static_campaign(campaign_id):
    """Renders individual campaign and saves it to S3"""

    campaign_type = ContentType.objects.get_for_model(Campaign)

    try:
        campaign = Campaign.objects.get(id=campaign_id)

    except Campaign.DoesNotExist:
        logger.error("Campaign #{0} does not exist".format(campaign_id))
        return

    rendered_content = [
        ("index.html", "CD", render_campaign(campaign)),
        ("mobile.html", "CM", render_campaign(campaign, mode="mobile"))
    ]

    for s3_file_name, log_key, page_content in rendered_content:

        # if we think this static page already exists, skip to the next one
        try:
            log_entry = StaticLog.objects.get(
                content_type=campaign_type, object_id=campaign.id, key=log_key)

            continue

        # otherwise, render and upload it
        except StaticLog.DoesNotExist:

            s3_path = "{0}/{1}".format(
                campaign.slug or campaign.id, s3_file_name)
            bucket_name = get_bucket_name(campaign.store.slug)

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
