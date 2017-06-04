from deploy import deploy
import celery
import database

from fabric.operations import open_shell
from fabric.api import env, task
from aws.api import get_instances

# set default user to be ec2-user for remote executions
env.user = 'ec2-user'
env.environment = 'dev'
env.shell = "/usr/bin/zsh -l -i -c" # interactive login shell, so .zshrc is loaded
env.forward_agent = True # cause people don't like having their SSH config setup in the same way as me

@task
def production():
    """ run on one of the production web servers """
    env.environment = 'production'
    env.hosts = production_all()[-1:]


@task
def stage():
    """ run on one of the test web servers """
    env.environment = 'stage'
    env.hosts = [i.public_dns_name for i in get_instances('secondfunnel-stage')][-1:]


@task
def production_all():
    """ run on ALL of the production web servers """
    env.environment = 'production'
    env.hosts = [i.public_dns_name for i in get_instances('secondfunnel-production')]
    return env.hosts


@task(alias='ssh')
def shell():
    """ssh to the selected environment"""
    open_shell()
