from celery import Celery, group
from celery.utils import noop
from celery.utils.log import get_task_logger

from django.conf import settings
from apps.intentrank.utils import ajax_jsonp

from apps.static_pages.aws_utils import sqs_poll

celery = Celery()
logger = get_task_logger(__name__)


def fetch_queue(queue=None):
    """Run something if the poll detects any messages in any queues
    that are managed by the Campaign Manager.

    """
    # these methods are locally imported for use as SQS callbacks
    from apps.assets.tasks import handle_queue_items as handle_assets_queue_items
    from apps.pinpoint.tasks import handle_queue_items as handle_pinpoint_queue_items
    from apps.scraper.tasks import handle_queue_items as handle_scraper_queue_items

    results = {}

    if queue:  # fetch one queue
        queues = [queue]
    else:  # fetch all queues
        queues = settings.AWS_SQS_POLLING_QUEUES

    for queue in queues:
        if not queue:  # so, a None queue can exist
            continue

        region_name = queue.get('region_name', settings.AWS_SQS_REGION_NAME)
        results[region_name] = results.get(region_name, {})

        queue_name = queue.get('queue_name', settings.AWS_SQS_QUEUE_NAME)
        queue_results = results[region_name].get(queue_name, [])

        handler_name = queue['handler']  # e.g. handle_items

        handler = locals().get(handler_name, noop)  # e.g. <function handle_items>
        try:
            queue_results.append(sqs_poll(callback=handler,
                region_name=region_name, queue_name=queue_name))
        except (AttributeError, ValueError) as err:  # (no such queue)
            queue_results.append({err.__class__.__name__: err.message})

        # queue finished, here are the results
        results[region_name][queue_name] = queue_results
    return results


@celery.task
def poll_queues():
    """periodic task for fetch_queue."""
    return ajax_jsonp(fetch_queue())
