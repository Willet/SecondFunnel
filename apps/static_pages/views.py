from datetime import datetime
import gzip
import json
import mimetypes
import StringIO
import sys
import traceback
import uuid

from BeautifulSoup import BeautifulSoup
import re
from django.conf import settings
from django.utils.encoding import smart_unicode
from apps.contentgraph.models import get_contentgraph_data, call_contentgraph

from apps.intentrank.utils import ajax_jsonp
from apps.pinpoint.utils import read_remote_file
from apps.static_pages.aws_utils import sns_notify, download_from_bucket, upload_to_bucket, s3_key_exists, copy_across_bucket, create_bucket_website_alias, copy_within_bucket
from apps.static_pages.tasks import (create_bucket_for_store_now,
                                     generate_static_campaign_now)

from secondfunnel.settings.test import INTENTRANK_BASE_URL as test_ir, \
    AWS_STORAGE_BUCKET_NAME as test_storage_bucket_name, \
    INTENTRANK_CONFIG_BUCKET_NAME as test_irconfig_bucket_name
from secondfunnel.settings.production import INTENTRANK_BASE_URL as prod_ir, \
    AWS_STORAGE_BUCKET_NAME as prod_storage_bucket_name, \
    INTENTRANK_CONFIG_BUCKET_NAME as prod_irconfig_bucket_name

def generate_static_campaign(request, store_id, campaign_id):
    """Manual stimulation handler: re-save a campaign.

    Campaign *will* be regenerated despite having a static log entry.

    This calls generate_static_campaign_now, the function-equivalent.
    A celery task for this function is also available in tasks.py.

    @deprecated: once all code is transitioned to the /graph/v1/ URL,
                 this one will no longer exist.

    @param [{string}] callback: jsonp callback (defaults to "callback")
    @returns {jsonp} the result key is true if succeeded, false if failed
    """
    (result, status) = (None, 200)
    try:
        create_bucket_for_store_now(store_id, force=True)
    except:
        pass  # bucket might already exist

    try:
        campaign_returns = generate_static_campaign_now(
            store_id, campaign_id, ignore_static_logs=True)
    except ValueError, err:
        _, exception, _ = sys.exc_info()
        stack = traceback.format_exc().splitlines()

        result = {
            'result': {
                'success': False,
                'reason': 'ContentGraph 404? {0}'.format(err.message),
                'traceback': '\n'.join(stack)
            }
        }
        status = 404

        # send a 'task incomplete' message to SNS.
        sns_notify(message=json.dumps({
           "page-id": "-1",
           "status": "failed",
        }), dev_suffix=True)
    except (Exception, BaseException), err:  # for other reasons... failed
        _, exception, _ = sys.exc_info()
        stack = traceback.format_exc().splitlines()

        result = {
            'result': {
                'success': False,
                'reason': str(err.message),
                'traceback': '\n'.join(stack)
            }
        }
        status = 500

        # send a 'task incomplete' message to SNS.
        sns_notify(message=json.dumps({
           "page-id": "-1",
           "status": "failed",
        }), dev_suffix=True)
    else:  # succeeded
        result = {
            'result': {
                'success': True,
                'campaign': {
                    'id': campaign_returns['campaign'].get('id', -1),
                    'url': campaign_returns['campaign'].get('url', ''),
                    'backup_results': campaign_returns['campaign'].get('backupResults', []),
                    'initial_results': campaign_returns['campaign'].get('initialResults', []),
                    'last_modified': campaign_returns['campaign'].get('last-modified', 0),
                },
                's3_path': campaign_returns.get('s3_path', ''),
                'bucket_name': campaign_returns.get('bucket_name', ''),
                'bytes_written': campaign_returns.get('bytes_written', 0),
            }
        }

        # send a 'task complete' message to SNS.
        sns_notify(message=json.dumps({
           "page-id": campaign_returns['campaign'].get('id', -1),
           "status": "successful",
        }), dev_suffix=True)


    return ajax_jsonp(result, request.GET.get('callback', None),
                      status=status)


def transfer_static_campaign(store_id, page_id):
    """Moves a test page in a test bucket to a production bucket,
    copying its IR config with it.

    Moving a page from production to test makes no sense, and is not
    implemented.

    For safety reasons, although dev->production transfers are possible,
    no uploads are performed through the dev campaign manager.

    :raises AttributeError, KeyError, IndexError, ValueError
    """
    # a date format with no colons or decimals in it
    now_suffix = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    results = {  # function return, for knowing what actually happened
        'success': True, 'store_id': store_id, 'page_id': page_id
    }

    cg_page_data = call_contentgraph('/store/{0}/page/{1}'.format(
        store_id, page_id))
    if not (cg_page_data and cg_page_data.get('store-id')):
        raise KeyError("Page {0} could not be retrieved")
    if not cg_page_data.get('url'):
        raise ValueError("Page {0} does not have a URL, and cannot be "
                         "transferred to production.")

    store_id = cg_page_data['store-id']  # more reliable value
    cg_store_data = call_contentgraph('/store/{0}'.format(store_id))
    if not cg_store_data:
        raise KeyError("Store {0} could not be retrieved")
    if not cg_store_data.get('public-base-url'):
        raise ValueError("Store {0} does not have a public-base-url yet. "
                         "Please create test and production website buckets "
                         "for this store.")

    ir_config_filename = '{0}.config.gz'.format(page_id)
    results['ir_config_filename'] = ir_config_filename
    if not s3_key_exists(bucket_name=test_irconfig_bucket_name,
                         filename=ir_config_filename):
        raise ValueError("Test IRConfig {0} does not exist "
                         "in the test bucket!".format(ir_config_filename))

    # public-base-url from content graph is always the production bucket name.
    # extract 'test-gap.secondfunnel.com' from http:// ... /
    # raises IndexError
    results['prod_bucket_name'] = prod_bucket_name = re.match(
        "(?:https?://)?([^/]+)", cg_store_data.get('public-base-url')).group(1)

    if not prod_bucket_name:
        raise ValueError("prod_bucket_name invalid")

    # see https://therealwillet.hipchat.com/history/room/115122/2014/01/28#15:27:21
    if 'test-' in prod_bucket_name:
        raise ValueError("public-base-url for this store contains 'test-'!")

    # resolve production bucket name by removing the test prefix that we add
    results['test_bucket_name'] = test_bucket_name = \
        "test-{0}".format(prod_bucket_name)
    results['test_s3_key'] = test_s3_key = \
        "{0}/index.html".format(cg_page_data['url'])

    # check if test page exists
    test_page = download_from_bucket(test_bucket_name, test_s3_key)

    # attempt to decompress our saved page, if it was compressed.
    try:
        data = StringIO.StringIO(test_page)
        gzipper = gzip.GzipFile(fileobj=data)
        test_page = gzipper.read()
    except IOError:  # "Not a gzipped file"
        pass  # already unzipped

    # locate all script tags on the page
    prod_page_source = smart_unicode(test_page)
    test_page_parsed = BeautifulSoup(test_page)
    script_tags = [tag.extract() for tag in test_page_parsed.findAll('script')]
    if not script_tags:
        raise AttributeError("Cannot modify IRSource: no script tags on this page")

    # PAGES_INFO can either be inline, or in an external script
    for script_tag in script_tags:
        script_type = script_tag.get('type')
        if script_type and 'template' in script_type:
            continue  # skip processing underscore template script tags

        if script_tag.get('src'):  # is external script
            script_contents = read_remote_file(script_tag.get('src'))

            if not script_contents:
                continue  # blank external tag
        else:  # is inline script, or is blank script (!script_tag.contents)
            # if the script is inline, then replacing the page source
            # will also replace this
            continue

        # why does a test page have a reference to the production ir?
        # throw exception to be safe.
        if prod_ir in script_contents:
            raise ValueError("Found unexpected reference to IR production "
                             "on test page")
        elif not test_ir in script_contents:  # irrelevant script
            continue

        # script_contents definitely contains http://intentrank-test.elasticbeanstalk.com
        script_contents = script_contents.replace(test_ir, prod_ir)
        # script_contents definitely contains http://intentrank.elasticbeanstalk.com

        # save the new script, calling it whatever we want, as long as
        # it doesn't already exist
        new_script_s3_key = ''  # bucket key always exists
        while s3_key_exists(settings.AWS_STORAGE_BUCKET_NAME, new_script_s3_key):
            new_script_s3_key = 'CACHE/{0}.js'.format(uuid.uuid4())

        # if not == 0 bytes written
        if not upload_to_bucket(bucket_name=prod_storage_bucket_name,
            filename=new_script_s3_key, content=script_contents,
            content_type=mimetypes.MimeTypes().guess_type(new_script_s3_key)[0],
            public=True, do_gzip=False):
            raise IOError("Could not write modified JS file to S3!")

        # overwrite old tag with new tag
        prod_page_source = prod_page_source.replace(script_tag.get('src'),
            'https://s3.amazonaws.com/{0}/{1}'.format(prod_storage_bucket_name,
                                                      new_script_s3_key))

    # replace all inline references to IR test to IR prod, but
    # do not overwrite existing production page before IRConfig copied over
    prod_page_source = prod_page_source.replace(test_ir, prod_ir)

    # backup the IR config
    copy_within_bucket(bucket_name=prod_irconfig_bucket_name,
                       from_filename=ir_config_filename,
                       to_filename="{0}.bak.{1}".format(ir_config_filename,
                                                        now_suffix),
                       overwrite=True)

    copy_across_bucket(source_bucket_name=test_irconfig_bucket_name,
                       dest_bucket_name=prod_irconfig_bucket_name,
                       filename=ir_config_filename,
                       overwrite=True)

    # backup the current index page
    if s3_key_exists(bucket_name=prod_bucket_name, filename=test_s3_key):
        copy_within_bucket(bucket_name=prod_bucket_name,
                           from_filename=test_s3_key,
                           to_filename="{0}.bak.{1}".format(test_s3_key,
                                                            now_suffix),
                           overwrite=True)

    # if line above didn't fail, overwrite production page
    results['bytes_written'] = bytes_written = \
        upload_to_bucket(bucket_name=prod_bucket_name,
            filename=test_s3_key, content=prod_page_source,
            content_type=mimetypes.MimeTypes().guess_type(test_s3_key)[0],
            public=True, do_gzip=True)

    try:  # if the bucket isn't in route53 already, make it so
        if 'secondfunnel.com' in prod_bucket_name:  # hosted solution
            create_bucket_website_alias(dns_name=prod_bucket_name,
                                        bucket_name=prod_bucket_name)
    except:
        pass

    if not bytes_written:
        raise IOError("Could not write modified JS file to S3!")

    return results
