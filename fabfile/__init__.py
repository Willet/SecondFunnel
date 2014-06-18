from deploy import deploy
import celery
import database

from fabric.api import env, task
from aws.api import get_instances

@task
def production():
    """ run on one of the production web servers """
    env.hosts = all_production[-1:]


@task
def test():
    """ run on one of the test web servers """
    env.hosts = [i.public_dns_name for i in get_instances('tng-test2')][-1:]


@task
def production_all():
    """ run on ALL of the production web servers """
    env.hosts = [i.public_dns_name for i in get_instances('tng-master2')]
