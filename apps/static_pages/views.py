import StringIO
import gzip
import json
import sys
import traceback

import BeautifulSoup
import re
from apps.contentgraph.models import get_contentgraph_data

from apps.intentrank.utils import ajax_jsonp
from apps.static_pages.aws_utils import sns_notify, download_from_bucket
from apps.static_pages.tasks import (create_bucket_for_store_now,
                                     generate_static_campaign_now)


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
        }))
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
        }))
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
        }))


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
    cg_page_data = get_contentgraph_data('/store/{0}/page/{1}'.format(
        store_id, page_id))
    if not cg_page_data and cg_page_data.get('store-id'):
        raise KeyError("Page {0} could not be retrieved")
    if not cg_page_data.get('url'):
        raise ValueError("Page {0} does not have a URL, and cannot be "
                         "transferred to production.")

    store_id = cg_page_data['store-id']  # more reliable value
    cg_store_data = get_contentgraph_data('/store/{0}'.format(store_id))
    if not cg_store_data:
        raise KeyError("Store {0} could not be retrieved")
    if not cg_store_data.get('public-base-url'):
        raise ValueError("Store {0} does not have a public-base-url yet. "
                         "Please create test and production website buckets "
                         "for this store.")

    # public-base-url from content graph is always the production bucket name.
    # extract 'test-gap.secondfunnel.com' from http:// ... /
    # raises IndexError
    prod_bucket_name = re.match("(?:https?://)?([^/]+)", cg_store_data.get(
        'public-base-url')).group(1)

    # see https://therealwillet.hipchat.com/history/room/115122/2014/01/28#15:27:21
    if 'test-' in prod_bucket_name:
        raise ValueError("public-base-url for this store contains 'test-'!")

    # resolve production bucket name by removing the test prefix that we add
    test_bucket_name = "test-{0}".format(prod_bucket_name)
    test_s3_key = "{0}/index.html".format(cg_page_data['url'])

    # check if test page exists
    test_page = download_from_bucket(test_bucket_name, test_s3_key)

    # attempt to decompress our saved page, if it was compressed.
    try:
        data = StringIO.StringIO(test_page)
        gzipper = gzip.GzipFile(fileobj=data)
        test_page = gzipper.read()
    except IOError:  # "Not a gzipped file"
        pass

    BeautifulSoup

    return test_page
