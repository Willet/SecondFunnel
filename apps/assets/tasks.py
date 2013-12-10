import json
from mock import MagicMock


# one day
TileGenerator = MagicMock()


def handle_product_queue_items(messages):
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

    @type messages {List} <boto.sqs.message.Message instance>
    @returns any JSON-serializable
    """
    results = []

    for msg in messages:
        try:
            message = json.loads(msg.get_body())
        except (TypeError, ValueError) as err:
            # safeguard for "No JSON object could be decoded"
            results.append({err.__class__.name: err.message})
            continue

        if not 'product-id' in message:
            # don't know what to update
            results.append({'malformed-message': 'missing product-id'})
            continue

        # whether or not updated-fields exists to tell us which tiles
        # -really- need updating is currently inconsequential
        # if 'updated-fields' in message: else:

        # run the TileGenerator to update the changed tiles
        TileGenerator.update_tiles(product_id=message['product-id'])
        results.append({'scheduled-tiles-for-product': message['product-id']})

    return results


def handle_content_queue_items(messages):
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
    results = []

    for msg in messages:
        try:
            message = json.loads(msg.get_body())
        except (TypeError, ValueError) as err:
            # safeguard for "No JSON object could be decoded"
            results.append({err.__class__.name: err.message})
            continue

        if not 'content-id' in message:
            # don't know what to update
            results.append({'malformed-message': 'missing content-id'})
            continue

        # whether or not updated-fields exists to tell us which tiles
        # -really- need updating is currently inconsequential
        # if 'updated-fields' in message: else:

        # run the TileGenerator to update the changed tiles
        TileGenerator.update_tiles(content_id=message['content-id'])
        results.append({'scheduled-tiles-for-content': message['content-id']})

    return results
