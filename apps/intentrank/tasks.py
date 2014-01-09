import json

from apps.api.decorators import (require_keys_for_message,
                                 validate_json_deserializable)
from apps.static_pages.tasks import generate_static_campaign_now


@validate_json_deserializable
@require_keys_for_message('store-id', 'page-id')
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
    message = json.loads(message)

    store_id = message.get('store-id')
    page_id = message.get('page-id')

    try:
        generate_static_campaign_now(store_id=store_id,
            campaign_id=page_id)

        return {'generated-page': page_id}
    except BaseException as err:
        # fails for whatever reason, work on the next page
        return {err.__class__.__name__: err.message}
