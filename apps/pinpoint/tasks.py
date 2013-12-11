import json
from mock import MagicMock

from apps.api.decorators import validate_json_deserializable

# one day
IRConfigGenerator = MagicMock()


def handle_tile_generator_update_notification_messages(messages):
    """
    Messages are fetched from an SQS queue and processed by this function.

    CM-127: There are two types of event that can be received.
    The first occurs when a single tile is updated and the second
    when all tiles for a page are updated.

    Each queue entry will contain a record such as:

    {
       "page-id": "1", [sic]
    }

    or for single tiles

    {
       "tile-id": "1", [sic]
    }

    Once this event has been received the CampaignManger will need to
    schedule the IRConfigGenerator to update the IR config.

    @type messages {List} <boto.sqs.message.Message instance>
    @returns any JSON-serializable
    """
    @validate_json_deserializable
    def handle_message(message):
        message = json.loads(message)

        if 'tile-id' in message:
            IRConfigGenerator.update_tile(tile_id=message['tile-id'])
            return {'scheduled-tile': message['tile-id']}

        if 'page-id' in message:
            IRConfigGenerator.update_page(tile_id=message['page-id'])
            return {'scheduled-page': message['page-id']}

    messages = [msg.get_body() for msg in messages]

    return map(handle_message, messages)
