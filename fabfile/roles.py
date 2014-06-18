from fabric.api import env
from aws.api import get_instances


def production():
    env.hosts = all_production[-1:]


def test():
    env.hosts = [i.public_dns_name for i in get_instances('tng-test2')][-1:]


def all_production():
    env.hosts = [i.public_dns_name for i in get_instances('tng-master2')]
