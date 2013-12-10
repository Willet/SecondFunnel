from celery import Celery, group
from celery.utils import noop
from celery.utils.log import get_task_logger

from django.conf import settings
from apps.intentrank.utils import ajax_jsonp

from apps.static_pages.aws_utils import sqs_poll

celery = Celery()
logger = get_task_logger(__name__)


def fetch_queue(queue=None, interval=None):
    """Run something if the poll detects any messages in any queues
    that are managed by the Campaign Manager.

    @param interval {int} number of seconds that this poll is being made.
    """
    # these methods are locally imported for use as SQS callbacks
    from apps.assets.tasks import (handle_content_queue_items,
                                   handle_product_queue_items)
    from apps.intentrank.tasks import handle_queue_items as \
        handle_ir_config_queue_items
    from apps.pinpoint.tasks import handle_queue_items as \
        handle_tile_generator_queue_items
    from apps.static_pages.tasks import handle_queue_items as \
        handle_page_generator_queue_items

    results = {}

    # corresponding queues need to be defined in settings.AWS_SQS_POLLING_QUEUES
    handlers = {
        'handle_content_queue_items': handle_content_queue_items,
        'handle_product_queue_items': handle_product_queue_items,
        'handle_ir_config_queue_items': handle_ir_config_queue_items,
        'handle_tile_generator_queue_items': handle_tile_generator_queue_items,
        'handle_page_generator_queue_items': handle_page_generator_queue_items,
    }

    if queue:  # fetch one queue
        queues = [queue]
    else:  # fetch all queues
        queues = settings.AWS_SQS_POLLING_QUEUES

    for queue in queues:
        if not queue:  # so, a None queue can exist
            continue

        # not a queue that this poll should run.
        if interval and interval != queue.get('interval', 60):
            continue

        region_name = queue.get('region_name', settings.AWS_SQS_REGION_NAME)
        results[region_name] = results.get(region_name, {})

        queue_name = queue.get('queue_name', settings.AWS_SQS_QUEUE_NAME)
        queue_results = results[region_name].get(queue_name, [])

        handler_name = queue['handler']  # e.g. handle_items

        handler = handlers.get(handler_name, noop)  # e.g. <function handle_items>
        try:
            queue_results.append(sqs_poll(callback=handler,
                region_name=region_name, queue_name=queue_name))
        except (AttributeError, ValueError) as err:  # (no such queue)
            queue_results.append({err.__class__.__name__: err.message})

        # queue finished, here are the results
        results[region_name][queue_name] = queue_results
    return results


@celery.task
def poll_queues(interval=60):
    """periodic task for fetch_queue.

    @param interval {int} number of seconds that this poll is being made.
    """
    return ajax_jsonp(fetch_queue(interval=interval))
