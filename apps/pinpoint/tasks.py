"""
Various PinPoint celery tasks: static pages, asset manager, etc
"""

import re
import urllib2
from urlparse import urlunparse

from celery import task, group
from celery.utils.log import get_task_logger

from django.core.files.base import ContentFile, File
from django.conf import settings

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError

from apps.pinpoint.models import Campaign
from apps.pinpoint.utils import render_campaign

# TODO: make use of logging, instead of suppressing errors as is done now
logger = get_task_logger(__name__)


@task()
def generate_static_campaigns():
    """Creates a group of tasks to generate/save campaigns,
    and runs them in parallel"""

    campaigns = Campaign.objects.filter(has_static_copy=False)

    task_group = group(generate_static_campaign.s(c.id) for c in campaigns)

    task_group.apply_async()


@task()
def generate_static_campaign(campaign_id):
    """Renders individual campaign and saves it to S3"""

    try:
        campaign = Campaign.objects.get(id=campaign_id)

    except Campaign.DoesNotExist:
        logger.error("Campaign #{} does not exist".format(campaign_id))
        return

    rendered_content = render_campaign(campaign)
    save_to_static_storage(campaign, rendered_content)


@task()
def upload_static(bucket, static_name):
    url = "{0}{1}".format(settings.STATIC_URL, static_name)
    logger.info("Uploading {}".format(url))

    try:
        content = urllib2.urlopen(url)

    except urllib2.HTTPError:
        logger.warning("Couldn't open {}".format(url))

    else:
        obj = Key(bucket)
        obj.key = static_name
        obj.set_contents_from_file(content)


def save_to_static_storage(campaign, content):
    """Saves rendered campaign to S3"""

    conn = S3Connection(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY
    )

    filename = "{}/index.html".format(campaign.id)

    if settings.DEBUG:
        bucket_name = settings.STATIC_CAMPAIGNS_BUCKET_NAME
    else:
        bucket_name = "{}.secondfunnel.com".format(campaign.store.slug)

    try:
        bucket = conn.get_bucket(bucket_name)

    except S3ResponseError:
        bucket = conn.create_bucket(bucket_name)

    obj = Key(bucket)
    obj.key = filename
    obj.set_contents_from_string(
        content.encode("utf-32"),
        headers={"Content-Type": "text/html"}
    )
    obj.set_acl('public-read')
