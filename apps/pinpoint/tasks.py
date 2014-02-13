import json

from celery import Celery
from celery.utils.log import get_task_logger

from apps.api.decorators import (validate_json_deserializable,
                                 require_keys_for_message)
from apps.api.views import generate_ir_config


celery = Celery()
logger = get_task_logger(__name__)

@validate_json_deserializable
@require_keys_for_message(['storeId', 'pageId'])
def handle_tile_generator_update_notification_message(message):
    """
    Messages are fetched from an SQS queue and processed by this function.

    CM-127: There are two types of event that can be received.
    The first occurs when a single tile is updated and the second
    when all tiles for a page are updated.

    Each queue entry will contain a record such as:

    {
       "pageId": "1",
       "storeId": "2"  [in consideration]
    }

    or for single tiles

    {
       "tileId": "1",
       "pageId": "2",  [in consideration]
       "storeId": "3"  [in consideration]
    }

    Once this event has been received the CampaignManger will need to
    schedule the IRConfigGenerator to update the IR config.

    @type message {boto.sqs.message.Message}
    @returns any JSON-serializable
    """
    message = json.loads(message)

    store_id = message['storeId']
    page_id = message['pageId']

    logger.info('Queueing IRConfig {0} generation now!'.format(page_id))
    # caller handles error
    generate_ir_config(store_id=store_id, ir_id=page_id)

    return {'scheduled-page': page_id}
