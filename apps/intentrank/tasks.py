import json

from celery import Celery
from celery.utils.log import get_task_logger

from apps.api.decorators import (validate_json_deserializable,
                                 require_keys_for_message)
from apps.static_pages.tasks import generate_static_campaign_now


celery = Celery()
logger = get_task_logger(__name__)


@validate_json_deserializable
@require_keys_for_message(['storeId', 'pageId'])
def handle_ir_config_update_notification_message(message):
    """
    Messages are fetched from an SQS queue and processed by this function.

    CM-128: When the IRConfigGenerator finishes generating an IntentRank
    configuration (...) the CampaignManager to listen for and process incoming
    event notifications from the IRConfigGenerator.

    Each event will have a format such as.
    {
       "page-id": "1", [sic*]
    }

    * a 'store-id' key has been requested.

    This event can be used to updated the timestamp of when the IRConfig was
    last generated to ensure that Ir configuration are not generated too
    frequently. In the future we may want to use this event to push the
    configuration to individual IR instances.

    @type message {boto.sqs.message.Message}
    @returns any JSON-serializable
    """
    from apps.api.resources import ContentGraphClient  # circular loop
    message = json.loads(message)

    store_id = message['storeId']
    page_id = message['pageId']

    r = ContentGraphClient.store(store_id).page(page_id)\
        .PATCH(params=json.dumps({'ir-stale': 'false'}))
    if r.status_code != 200:
        logger.warn("Failed to make ir-stale for (store,page) = (%s,%s)" % (store_id, page_id))

    logger.info('Generating page {0} now!'.format(page_id))
    # caller handles error
    generate_static_campaign_now(
        store_id=store_id,
        campaign_id=page_id,
        ignore_static_logs=True)

    return {'generated-page': page_id}
