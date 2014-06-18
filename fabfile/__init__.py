from deploy import deploy
import celery
import database

from fabric.api import env, task
from aws.api import get_instances

# set default user to be ec2-user for remote executions
env.user = 'ec2-user'
env.environment = 'dev'

@task
def production():
    """ run on one of the production web servers """
    env.environment = 'production'
    env.hosts = production_all()[-1:]


@task
def test():
    """ run on one of the test web servers """
    env.environment = 'stage'
    env.hosts = [i.public_dns_name for i in get_instances('tng-test2')][-1:]


@task
def production_all():
    """ run on ALL of the production web servers """
    env.environment = 'production'
    env.hosts = [i.public_dns_name for i in get_instances('tng-master2')]
    return env.hosts
