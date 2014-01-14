from datetime import timedelta

from celery import Celery
from celery.task import periodic_task
from celery.utils import noop
from celery.utils.log import get_task_logger


celery = Celery()
logger = get_task_logger(__name__)

@celery.task
def poll(*args, **kwargs):
    logger.info('polling!!')
    return noop()

@periodic_task(run_every=timedelta(seconds=2))
def every_2_seconds():
    print("Running periodic task!")
