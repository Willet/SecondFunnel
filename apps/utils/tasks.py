from celery import Celery

from celery.utils import noop
from celery.utils.log import get_task_logger


celery = Celery()
logger = get_task_logger(__name__)

@celery.task
def debug(*args, **kwargs):
    logger.info('debug!!')
    return noop()
