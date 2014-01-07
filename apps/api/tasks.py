import json

from celery import Celery
from celery.utils import noop
from celery.utils.log import get_task_logger

from django.conf import settings
from apps.intentrank.utils import ajax_jsonp
from apps.contentgraph.models import get_contentgraph_data

from apps.static_pages.aws_utils import sqs_poll, SQSQueue

celery = Celery()
logger = get_task_logger(__name__)


def fetch_queue(queue=None, interval=None):
    """Run something if the poll detects any messages in any queues
    that are managed by the Campaign Manager.

    @param queue {dict|None}  a queue from AWS_SQS_POLLING_QUEUES.
    @param interval {int} number of seconds that this poll is being made.
                          -1 means "fetch regardless".
    """
    # these methods are locally imported for use as SQS callbacks
    from apps.assets.tasks import (handle_content_update_notification_message,
                                   handle_product_update_notification_message)
    from apps.intentrank.tasks import handle_ir_config_update_notification_message
    from apps.pinpoint.tasks import handle_tile_generator_update_notification_message
    from apps.static_pages.tasks import handle_page_generator_notification_message
    from apps.scraper.tasks import handle_scraper_notification_message

    queue_to_fetch = queue
    results = {}

    # corresponding queues need to be defined in settings.AWS_SQS_POLLING_QUEUES
    handlers = {
        'handle_content_update_notification_message':
            handle_content_update_notification_message,
        'handle_product_update_notification_message':
            handle_product_update_notification_message,
        'handle_ir_config_update_notification_message':
            handle_ir_config_update_notification_message,
        'handle_tile_generator_update_notification_message':
            handle_tile_generator_update_notification_message,
        'handle_page_generator_notification_message':
            handle_page_generator_notification_message,
        'handle_scraper_notification_message':
            handle_scraper_notification_message
    }

    regions = settings.AWS_SQS_POLLING_QUEUES
    for region_name, queues in regions.iteritems():
        results[region_name] = results.get(region_name, {})

        # queues be <list>
        for queue_name, queue in queues.iteritems():
            results[region_name][queue_name] = []

            if queue_to_fetch and queue_name != queue_to_fetch['queue_name']:
                continue  # fetch one queue, name mismatch, skip this queue

            # not a queue that this poll should run.
            if interval and interval != -1 and interval != queue.get('interval', 60):
                continue


            handler_name = queue['handler']  # e.g. handle_items
            handler = handlers.get(handler_name, noop)  # e.g. <function handle_items>

            try:
                messages = sqs_poll(region_name=region_name,
                                    queue_name=queue_name)
            except BaseException as err:  # something went wrong
                results[region_name][queue_name].append(
                    {err.__class__.__name__: err.message})
                continue

            # call handler on each message, and save their results
            for message in messages:
                try:
                    results[region_name][queue_name].append(
                        handler(message.get_body()))

                    # you have handled the message. dequeue the message.
                    message.delete()

                except BaseException as err:
                    # message failed, leave message in queue so someone else
                    # can try it again
                    results[region_name][queue_name].append(
                        {err.__class__.__name__: err.message,
                         'message': message.get_body()})

    return results


@celery.task
def poll_queues(interval=60):
    """periodic task for fetch_queue.

    @param interval {int} number of seconds that this poll is being made.
    """
    return ajax_jsonp(fetch_queue(interval=interval))

#Common.py has the config for how often this task should run
@celery.task
def queue_stale_tile_check():
    stores = get_contentgraph_data('/store?results=100000')['results']
    store_ids = []

    for store in stores:
        store_ids.append(store['id'])

    pages = []

    for store_id in store_ids:
        pages += get_contentgraph_data('/store/%s/page?results=100000' % store_id)['results']

    ouput_queue = SQSQueue(queue_name=settings.STALE_TILE_QUEUE_NAME)

    for page in pages:
        ouput_queue.write_message({
            'classname': 'com.willetinc.contentgraph.tiles.worker.GenerateStaleTilesWorkerTask',
            'conf': json.dumps({
                'pageId': page['id'],
                'storeId': page['store-id']
            })
        })