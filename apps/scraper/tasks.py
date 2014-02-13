from apps.api.decorators import validate_json_deserializable


@validate_json_deserializable
def handle_scraper_notification_message(message):
    """
    Messages are fetched from an SQS queue and processed by this function.

    @type message {boto.sqs.message.Message}
    @returns any JSON-serializable
    """

    return {}
