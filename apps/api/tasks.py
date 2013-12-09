from celery import Celery, group
from celery.utils import noop
from celery.utils.log import get_task_logger

from django.conf import settings

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

    if queue:  # fetch one queue
        queues = [queue]
    else:  # fetch all queues
        queues = settings.AWS_SQS_POLLING_QUEUES

    for queue in queues:
        if not queue:  # so, a None queue can exist
            continue

        handler_name = queue['handler']  # e.g. handle_items
        handler = locals().get(handler_name, noop)  # e.g. <function handle_items>
        sqs_poll(callback=handler,
            region_name=queue.get('region_name', settings.AWS_SQS_REGION_NAME),
            queue_name=queue.get('queue_name', settings.AWS_SQS_QUEUE_NAME))


@celery.task
def poll_queues():
    """periodic task for fetch_queue."""
    fetch_queue()
