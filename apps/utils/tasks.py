from celery import Celery

from celery.task.control import inspect
from celery.utils import noop
from celery.utils.log import get_task_logger


celery = Celery()
logger = get_task_logger(__name__)

@celery.task
def debug(*args, **kwargs):
    logger.info('debug!!')
    return noop()

def get_celery_worker_status():
    ERROR_KEY = "ERROR"
    try:
        insp = inspect()
        d = insp.stats()
        if not d:
            d = { ERROR_KEY: 'No running Celery workers were found.' }
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the (RabbitMQ/AmazonSQS) server is running.'
        d = { ERROR_KEY: msg }
    except ImportError as e:
        d = { ERROR_KEY: str(e)}
    return d