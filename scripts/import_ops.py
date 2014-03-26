"""
Allows jenkins (or whatever) to initiate a data import.
"""
from fabric.api import roles, run, cd, execute, settings, env, sudo, hide
from fabric.colors import green, yellow, red
from secondfunnel.settings import common as django_settings

import boto.ec2
import itertools


env.user = 'ec2-user'  # controls what "ssh ???@instance" runs


def get_ec2_conn():
    return boto.ec2.connect_to_region("us-west-2",
        aws_access_key_id=django_settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=django_settings.AWS_SECRET_ACCESS_KEY)


def flatten_reservations(reservations):
    """Seems to flatten ... something"""
    instances = [r.instances for r in reservations]
    chain = itertools.chain(*instances)

    return [i for i in list(chain)]


def get_instances(instance_type):
    """Gets instances belonging to specified instance type"""
    ec2 = get_ec2_conn()
    res = ec2.get_all_instances(filters={
        'tag:Name': 'tng-{0}2'.format(instance_type)
    })

    # we only want running instances
    return [i for i in flatten_reservations(res) if i.state in ['running', 'pending']]


def execute_importer(instance_type, store_id, full_size_images):
    """Runs "importer ..." in the instance"""

    # we only support two instance types
    # (since their names are linked to our environmental vars on workers
    supported_instance_types = ["test", "master"]
    if instance_type not in supported_instance_types:
        print red("Received instance type: {0}. It must be one of: {1}".format(
            instance_type, supported_instance_types))

    env_path = "/opt/python/current"
    project_path = "{0}/app".format(env_path)

    with cd(project_path):
        print green("Starting importer...")
        run("python manage.py importer {0} {1}".format(store_id,
            str(full_size_images).lower()))

    print green("Success!")


def importer(instance_type='test', store_id=38, full_size_images=False):
    """import from contentgraph{data_source} to tng-{instance_type}"""
    print green("Importing store {0} data from CG test to {1}...".format(
        store_id, instance_type))

    instances = get_instances(instance_type)
    instances_dns = [i.public_dns_name for i in instances]

    execute(execute_importer, instance_type, store_id, full_size_images,
            hosts=instances_dns)
