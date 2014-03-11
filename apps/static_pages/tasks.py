"""
Static pages celery tasks
"""

import os
import re
import uuid
import mimetypes
from urlparse import urlparse

from celery import Celery, group
from celery.utils import noop
from celery.utils.log import get_task_logger

from BeautifulSoup import BeautifulSoup, Comment
from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import smart_str

from apps.pinpoint.utils import read_remote_file
from apps.assets.models import Store
from apps.contentgraph.views import get_page, get_store, get_stores
from apps.intentrank.views import get_seeds
from apps.pinpoint.models import Campaign
from apps.static_pages.aws_utils import (create_bucket_website_alias, s3_key_exists,
    get_route53_change_status, sqs_poll, SQSQueue, upload_to_bucket)
from apps.static_pages.utils import (get_bucket_name, create_dummy_request,
                                     render_campaign)

from secondfunnel.settings.test import AWS_STORAGE_BUCKET_NAME as test_storage_bucket_name
from secondfunnel.settings.test import CLOUDFRONT_DOMAIN as cloudfront_domain


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

    RELEASE_LOCK()


@celery.task
def create_bucket_for_stores():
    stores = get_stores()

    task_group = group(create_bucket_for_store.s(s.id) for s in stores)

    task_group.apply_async()


@celery.task
def create_bucket_for_store(store_id):
    """The task version of the synchronous operation."""
    return create_bucket_for_store_now(store_id)


def create_bucket_for_store_now(store_id, force=False):
    if ACQUIRE_LOCK() or force:
        try:
            store = get_store(store_id, as_dict=True)

        except ValueError:
            logger.error("Store #{0} does not exist".format(store_id))
            return


        store_url = ''
        if store.get('public-base-url', False):
            url = urlparse(store.get('public-base-url')).hostname
            if url:
                store_url = url

        dns_name = get_bucket_name(store.get('slug'))
        bucket_name =  store_url or dns_name

        # check for dev/test prefix. This allows campaign.url from campaign maanger
        # to be a full secondfunnel.com url.
        if settings.ENVIRONMENT in ["test", "dev"]:
            if not bucket_name[:len(settings.ENVIRONMENT)] == settings.ENVIRONMENT:
                bucket_name = '{0}-{1}'.format(settings.ENVIRONMENT, bucket_name)

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



def handle_page_generator_notification_message(message):
    """
    Messages are fetched from an SQS queue and processed by this function.

    The Campaign Manager currently does nothing when page generation
    is complete.

    @type message {boto.sqs.message.Message}
    @returns None
    """
    pass


@celery.task
def generate_static_campaign(store_id, campaign_id, ignore_static_logs=False):
    """The task version of the synchronous operation."""
    logger.info("Generating campaign (Store #{0}, Page #{1})".format(store_id, campaign_id))
    return generate_static_campaign_now(store_id, campaign_id,
                                        ignore_static_logs)


def generate_local_campaign(store_id, campaign_id, page_content):
    root = os.getcwd()
    pinpoint_static = os.path.join(root, 'apps', 'pinpoint', 'static')
    campaign_path = os.path.join(pinpoint_static, 'campaigns')

    if not os.path.exists(campaign_path):
        try:
            os.mkdir(campaign_path)
        except OSError as err:  # you have no access to this directory.
            return

    store_path = os.path.join(campaign_path, str(store_id))

    if not os.path.exists(store_path):
        try:
            os.mkdir(store_path)
        except OSError as err:
            return

    html_path = os.path.join(store_path, '%s.html' % campaign_id)

    with open(html_path, 'wb') as html_file:
        try:
            html_file.write(smart_str(page_content))
        except Exception as e:
            pass #Fail gracefully

def generate_static_campaign_now(store_id, campaign_id, ignore_static_logs=False):
    """Renders individual campaign and saves it to S3."""

    try:
        campaign_dict = get_page(store_id=store_id, page_id=campaign_id,
                                 as_dict=True)

        # do -something- to turn ContentGraph JSON into a campaign object
        campaign = Campaign.from_json(campaign_dict)

        store_dict = get_store(store_id=store_id, as_dict=True)
        store = Store.from_json(store_dict)

    except ValueError, err:  # json.loads exception
        logger.error("Campaign #{0}: {1}".format(campaign_id, err.message))
        raise  # someone catch it

    dummy_request = create_dummy_request()

    # prepare the file name, static log, and the actual page
    log_key = "CD"

    page_content = render_campaign(store_id, campaign_id,
                                   get_seeds_func=get_seeds,
                                   request=dummy_request)

    # Add async to generated tags
    page_source_parsed = BeautifulSoup(page_content)
    # Determine which content can be gzipped and which cannot
    # Naive implementation, not to be trusted for all situations
    conditional_comments = page_source_parsed.findAll(text=lambda text: isinstance(text, Comment) and \
                                text.find('if') != -1)
    gzip_support = []

    for comment in conditional_comments:
        comment = unicode(comment) if unicode(comment).find('src') != -1 else \
                      (unicode(comment) + unicode(comment.findNextSibling()))
        if (comment.find('gte IE 9') > -1 or comment.find('gt IE 8') > -1):
            gzip_support.append((True, comment))
        else:
            gzip_support.append((False, comment))

    # Collect the script tags
    script_tags = [tag.extract() for tag in page_source_parsed.findAll('script')]

    if script_tags:
        for script_tag in script_tags:
            script_type = script_tag.get('type')
            old_script = str(script_tag)
            if script_type and 'template' in script_type:
                continue # skip processing templates

            src = script_tag.get('src')
            if not src:
                continue # ignore inline scripts

            can_gzip = False
            # http://stackoverflow.com/questions/2612802/how-to-clone-or-copy-a-list-in-python
            for index, (support, comment) in enumerate(gzip_support[:]): # check for gzip support
                if src in comment:
                    can_gzip, _ = gzip_support.pop(index)
                    break

            if can_gzip and settings.ENVIRONMENT != 'dev':
                # Can gzip this content, can't in dev as middleware serves
                content, _ = read_remote_file(src)
                new_script_s3_key = '' # bucket key
                while s3_key_exists(test_storage_bucket_name, new_script_s3_key):
                    new_script_s3_key = 'CACHE/{0}.js'.format(uuid.uuid4())

                # Ensure can upload to the test bucket
                if not upload_to_bucket(bucket_name=test_storage_bucket_name,
                    filename=new_script_s3_key, content=content,
                    content_type=mimetypes.MimeTypes().guess_type(new_script_s3_key)[0],
                    public=True, do_gzip=True):
                    raise IOError("Could not upload the gzipped JS file to S3!")

                # Force relative path
                src = '//{0}/{1}'.format(cloudfront_domain, new_script_s3_key)

            script_tag['src'] = re.sub(r'(http|https)://', '//', src)
            script_tag['async'] = "true"
            page_content = page_content.replace(old_script, str(script_tag), 1)

    # e.g. "shorts3/index.html"
    identifier = getattr(campaign, 'url', '') or \
                 getattr(campaign, 'slug', '') or \
                 getattr(campaign, 'id')

    s3_path = "{0}/index.html".format(identifier)

    store_url = ''
    # this will err intentionally if a store has no public base url
    url = urlparse(getattr(store, 'public-base-url')).hostname
    if url:
        store_url = url

    dns_name = get_bucket_name(store.slug)
    bucket_name =  store_url or dns_name

    # check for dev/test prefix. This allows campaign.url from campaign maanger
    # to be a full secondfunnel.com url.
    if settings.ENVIRONMENT in ["test", "dev"]:
        if not bucket_name[:len(settings.ENVIRONMENT)] == settings.ENVIRONMENT:
            bucket_name = '{0}-{1}'.format(settings.ENVIRONMENT, bucket_name)

    logger.info("Uploading campaign #{0} to {1}/{2}".format(
        campaign_id, bucket_name, s3_path))
    bytes_written = upload_to_bucket(
        bucket_name, s3_path, page_content, public=True)

    if bytes_written > 0:
        if settings.ENVIRONMENT == "dev":
            generate_local_campaign(store_id, campaign_id, page_content)
    # boto claims it didn't write anything to S3
    else:
        logger.error("Error uploading campaign #{0}: wrote 0 bytes".format(
            campaign_id))

    # return some kind of feedback
    return {
        's3_path': s3_path,
        'bucket_name': bucket_name,
        'campaign': campaign_dict,  # warning: contains store theme
        'store': store_dict,
        'bytes_written': bytes_written,
    }
