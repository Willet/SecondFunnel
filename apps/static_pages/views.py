import sys, traceback

from apps.intentrank.utils import ajax_jsonp
from apps.static_pages.tasks import (create_bucket_for_store_now,
                                     generate_static_campaign_now)


def regenerate_static_campaign(request, store_id, campaign_id):
    """Manual stimulation handler: re-save a campaign.

    Campaign *will* be regenerated despite having a static log entry.

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

    return ajax_jsonp(result, request.GET.get('callback', 'callback'),
                      status=status)