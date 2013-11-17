import json
from apps.contentgraph.views import proxy_store, proxy_page
from apps.page_generator.utils import get_or_create_bucket, generate_page
from apps.utils.views import json_response


def generate(request, store_id, page_id):
    store_json, _ = proxy_store(request, store_id, raw=True)
    store = json.loads(store_json)

    page_json = proxy_page(request, store_id, page_id)
    page = json.loads(page_json)

    get_or_create_bucket(store)

    generate_page(request, store, page)

    # What to return?
    return json_response()


    # (result, status) = (None, 200)
    # try:
    #     create_bucket_for_store_now(store_id, force=True)
    # except:
    #     pass  # bucket might already exist
    #
    # try:
    #     campaign_returns = generate_static_campaign_now(
    #         store_id, campaign_id, ignore_static_logs=True)
    # except ValueError, err:
    #     _, exception, _ = sys.exc_info()
    #     stack = traceback.format_exc().splitlines()
    #
    #     result = {
    #         'result': {
    #             'success': False,
    #             'reason': 'ContentGraph 404? {0}'.format(err.message),
    #             'traceback': '\n'.join(stack)
    #         }
    #     }
    #     status = 404
    # except (Exception, BaseException), err:  # for other reasons... failed
    #     _, exception, _ = sys.exc_info()
    #     stack = traceback.format_exc().splitlines()
    #
    #     result = {
    #         'result': {
    #             'success': False,
    #             'reason': str(err.message),
    #             'traceback': '\n'.join(stack)
    #         }
    #     }
    #     status = 500
    # else:  # succeeded
    #     result = {
    #         'result': {
    #             'success': True,
    #             'campaign': {
    #                 'id': campaign_returns['campaign'].get('id', -1),
    #                 'url': campaign_returns['campaign'].get('url', ''),
    #                 'backup_results': campaign_returns['campaign'].get('backupResults', []),
    #                 'initial_results': campaign_returns['campaign'].get('initialResults', []),
    #                 'last_modified': campaign_returns['campaign'].get('last-modified', 0),
    #             },
    #             's3_path': campaign_returns.get('s3_path', ''),
    #             'bucket_name': campaign_returns.get('bucket_name', ''),
    #             'bytes_written': campaign_returns.get('bytes_written', 0),
    #         }
    #     }
    #
    # return ajax_jsonp(result, request.GET.get('callback', 'callback'),
    #                   status=status)