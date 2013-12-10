import json
from mock import MagicMock

from apps.static_pages.tasks import generate_static_campaign_now

# one day
IRConfigGenerator = MagicMock()


def handle_ir_config_queue_items(messages):
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

    @type messages {List} <boto.sqs.message.Message instance>
    @returns any JSON-serializable
    """
    results = []

    for msg in messages:
        try:
            # each message is a page id
            message = json.loads(msg.get_body())
        except (TypeError, ValueError) as err:
            # safeguard for "No JSON object could be decoded"
            results.append({err.__class__.name: err.message})
            continue

        if not ('store-id' in message and 'page-id' in message):
            # don't know what to generate
            results.append({'malformed-message': 'missing page-id'})
            continue

        store_id = message.get('store-id')
        page_id = message.get('page-id')

        try:
            generate_static_campaign_now(store_id=store_id,
                                         campaign_id=page_id,
                                         ignore_static_logs=True)

            results.append({'generated-page': page_id})
        except BaseException as err:
            # fails for whatever reason, work on the next page
            results.append({err.__class__.__name__: err.message})

    return results
