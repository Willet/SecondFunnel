from django.conf import settings

from apps.api.decorators import check_login
from apps.api.tasks import fetch_queue
from apps.intentrank.utils import ajax_jsonp


@check_login
def check_queue(request, queue_name=None, region=settings.AWS_SQS_REGION_NAME):
    """Provides a URL to instantly poll an SQS queue, and, if a message is
    found, process it.
    """
    queue = None

    try:
        queue = settings.AWS_SQS_POLLING_QUEUES[region][queue_name]
    except KeyError as err:
        if queue_name:  # None queue is fine -- it then checks all queues
            raise ValueError('Queue by that name ({0}) is missing'.format(
                queue_name))

    try:
        queue_results = fetch_queue(queue=queue,
            interval=request.GET.get('interval', None))
        return ajax_jsonp(queue_results)
    except (AttributeError, ValueError) as err:
        # no queue or none queue
        return ajax_jsonp({err.__class__.__name__: err.message})
