

def handle_queue_items(messages):
    """
    Messages are fetched from an SQS queue and processed by this function.

    @type messages {List} <boto.sqs.message.Message instance>
    @returns any JSON-serializable
    """
    for message in messages:
        pass
    return {}
