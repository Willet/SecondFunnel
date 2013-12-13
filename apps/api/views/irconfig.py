import json
from boto.sqs.message import RawMessage
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from apps.api.decorators import request_methods, check_login
from apps.static_pages.aws_utils import SQSQueue


# Task?
# When does IR update?
# It updates when tiles are regenerated
@request_methods('POST')
@check_login
@never_cache
@csrf_exempt
def generate_ir_config_view(request, store_id, ir_id):
    """view for generating an IR config."""
    try:
        generate_ir_config(store_id=store_id, ir_id=ir_id)
        return HttpResponse(status=200, content='OK')
    except ValueError as err:
        return HttpResponse(status=500, content=err.message)


def generate_ir_config(store_id, ir_id):
    # Yes, it is weird that we have json dumps inside a payload
    # that will also be dumped, but this is how it is implemented.
    payload = {
        'classname': 'com.willetinc.intentrank.engine.config.worker.ConfigWriterTask',
        'conf': json.dumps({
            'storeId': store_id,
            'pageId': ir_id
        })
    }

    # Post to SQS Queue
    message = RawMessage()
    message.set_body(payload)

    queue_name = 'intentrank-configwriter-worker-queue'
    if settings.ENVIRONMENT in ['dev', 'test']:
        queue_name = '{queue}-{env}'.format(queue=queue_name,
                                            env='test')


    try:
        queue = SQSQueue(queue_name=queue_name)
    except ValueError, e:
        raise e.__class__(json.dumps({
            'error': 'No queue found with name {name}'.format(name=queue_name)
        }))

    queue.queue.set_message_class(RawMessage)
    queue.queue.write(message)
