import json
import calendar
from datetime import datetime

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

    if interval:  # convert things like u'5' to 5
        interval = int(interval)

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
    for region_name, queues in regions.iteritems():  # {'us-west-2': KVs}
        results[region_name] = results.get(region_name, {})

        # queues be <dict>
        for queue_name, queue in queues.iteritems():
            results[region_name][queue_name] = []

            if queue_to_fetch and queue_name != queue_to_fetch['queue_name']:
                continue  # fetch one queue, name mismatch, skip this queue

            # not a queue that this poll should run.
            if interval and interval != -1 and interval != queue.get('interval', 60):
                continue

            # this queue should be polled now -- poll it.
            handler_name = queue['handler']  # e.g. handle_items
            handler = handlers.get(handler_name, noop)  # e.g. <function handle_items>

            try:
                logger.info('Polling queue %s:%s!' % (region_name, queue_name))
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
def queue_stale_tile_check(*args):
    """Doesn't actually check for stale tiles.
    Tile Generator checks for stale tiles.
    """
    stores = get_contentgraph_data('/store?results=100000')['results']
    pages = []

    for store in stores:
        try:
           pages += get_contentgraph_data('/store/%s/page?results=100000' % store['id'])['results']
        except TypeError:
            logger.error('Store with id: %s failed to get pages from content graph.' % store['id'])

    output_queue = SQSQueue(queue_name=settings.STALE_TILE_QUEUE_NAME)

    for page in pages:
        stale_content = get_contentgraph_data('/page/%s/tile-config?stale=true&results=1' % page['id'])['results']

        if len(stale_content) > 0:
            logger.info('Pushing to tile service worker queue!')
            output_queue.write_message({
                'classname': 'com.willetinc.tiles.worker.GenerateStaleTilesWorkerTask',
                'conf': json.dumps({
                    'pageId': page['id'],
                    'storeId': page['store-id']
                })
            })

@celery.task
def queue_page_regeneration():
    """periodic task that checks for pages that need to be regenerated and
    queues them into IRConfigGenerator; a page needs to be regenerated if a
    tile and tile-config were removed.
    """
    # Local import to avoid issues with circular importation
    from apps.api.views import generate_ir_config
    # For now, 100000 is probably a safe value for the number of results, but ideally, we'd
    # want the ContentGraph to return a generator to handle pagination.
    stores = get_contentgraph_data('/store?results=100000')['results']
    threshold = 60

    for store in stores:
        # Get only the stale pages from the store, eventually this will be phased
        # to not need to iterate over stores.
        pages = get_contentgraph_data('/store/%s/page?results=100000&ir-stale=true' % store['id'])['results']
        for page in pages:
            data = get_contentgraph_data('/store/%s/page/%s' %(store['id'], page['id']))
            last_generated = calendar.timegm(datetime.utcnow().timetuple())
            payload = json.dumps({
                'ir-stale': 'false',
                'ir-last-generated': last_generated
            })
            # Don't patch if versions don't sync.  If that is the case, tasker will pick
            # it up on next poll.
            headers = {
                'consistent': 'true',
                'version': data['last-modified']
            }
            try:
                get_contentgraph_data('/store/%s/page/%s' %(store['id'], page['id']),
                                      headers=headers, method="PATCH", body=payload)
                # Ensure we aren't generating too often
                last_generated -= int(data['ir-last-generated'])
                if last_generated > threshold:
                    generate_ir_config(store['id'], page['id'])
            except Exception as e:
                logger.info(e)
