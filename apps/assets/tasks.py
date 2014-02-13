import json

from celery import Celery
from celery.utils.log import get_task_logger

from apps.api.decorators import (validate_json_deserializable,
                                 require_keys_for_message)

from apps.contentgraph.models import TileConfigObject


celery = Celery()
logger = get_task_logger(__name__)

@validate_json_deserializable
@require_keys_for_message(['storeId', 'productId'])
def handle_product_update_notification_message(message):
    """
    Messages are fetched from an SQS queue and processed by this function.

    CM-125: When a product update notification has been received the
    CampaignManager will need to update any tiles containing that product and
    run the TileGenerator to update the changed tiles.

    When a scraper updates a product record. More specifically
    when the product validator moves an updated product from scraped to live.
    And event will be queued.

    Each queue entry will contain a record such as:
    {
       "product-id": "1",
       "updated-fields": ["price", "name",...]
    }

    Once this event has been received the CampaignManger will need to
    schedule the IRConfigGenerator to update the IR config.

    The update-fields list can be used to determine if the change requires
    any tiles to be updated (...) I'm still debating whether to include
    the updated-fields field. (...)

    @type messages {boto.sqs.message.Message}
    @returns any JSON-serializable
    """
    message = json.loads(message)
    # whether or not updated-fields exists to tell us which tiles
    # -really- need updating is currently inconsequential
    # if 'updated-fields' in message: else:

    store_id = message['storeId']
    product_id = message['productId']

    # add an item to the TileGenerator's queue to have it updated
    tile_config_object = TileConfigObject(store_id=store_id)
    logger.info('Marking tiles for product {0} as stale!'.format(product_id))
    # caller handles error
    tile_config_object.mark_tile_for_regeneration(product_id=product_id)

    return {'scheduled-tiles-for-product': product_id}


@validate_json_deserializable
@require_keys_for_message(['storeId', 'contentId'])
def handle_content_update_notification_message(message):
    """
    CM-126: When a scraper updates a content record. When the scraper add
    a new piece of content an event will be queued.

    Each queue entry will contain a record such as:
    {
       "content-id": "1",
       "updated-fields": ["caption", "dominant-colour",...]
    }

    When a (message) is dequeued the campaign manager will need to determine
    which tiles need to be updated. (..) this event notifies any listeners
    of newly created content as well.

    The update-fields list can be used to determine if the change requires
    any tiles to be updated (...) I'm still debating whether to include
    the updated-fields field. (...)

    @type messages {List} <boto.sqs.message.Message instance>
    @returns any JSON-serializable
    """
    message = json.loads(message)

    # whether or not updated-fields exists to tell us which tiles
    # -really- need updating is currently inconsequential
    # if 'updated-fields' in message: else:

    store_id = message['storeId']
    content_id = message['contentId']

    # add an item to the TileGenerator's queue to have it updated
    tile_config_object = TileConfigObject(store_id=store_id)
    logger.info('Marking tiles for content {0} as stale!'.format(content_id))
    # caller handles error
    tile_config_object.mark_tile_for_regeneration(content_id=content_id)

    return {'scheduled-tiles-for-content': content_id}
