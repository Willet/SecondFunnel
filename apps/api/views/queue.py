from django.conf import settings

from apps.api.decorators import check_login
from apps.api.tasks import fetch_queue
from apps.intentrank.utils import ajax_jsonp


@check_login
def check_queue(request, queue_name):
    """Provides a URL to instantly poll an SQS queue, and, if a message is
    found, process it.
    """
    queue = None

    def get_default_queue_by_name(name, region=settings.AWS_SQS_REGION_NAME):
        """maybe this should be somewhere else if it is useful."""
        queues = settings.AWS_SQS_POLLING_QUEUES
        for queue in queues:
            if queue.get('region_name', None):
                if queue['region_name'] != region:
                    continue
            if queue.get('queue_name', None):
                if queue['queue_name'] != name:
                    continue
            if queue:
                return queue
        raise ValueError('Queue by that name ({0}) is missing'.format(name))

    try:
        queue = get_default_queue_by_name(queue_name)
        return ajax_jsonp(fetch_queue(queue))
    except (AttributeError, ValueError) as err:
        # no queue or none queue
        return ajax_jsonp({err.__class__.__name__: err.message})
