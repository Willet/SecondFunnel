"""
Automated deployment tasks
"""
from datetime import datetime
import os
from fabric.api import roles, run, cd, execute, settings, env, sudo, hide
from fabric.colors import green, yellow, red
from fabric.contrib import django
from fabric.decorators import hosts
from fabric.operations import local, get
from secondfunnel.settings import common as django_settings
from scripts.import_ops import importer as real_importer
from scripts.import_ops import scraper as real_scraper

import boto.ec2
import itertools
import time

env.user = 'ec2-user'

def prepend(filepath, content):
    data = ''
    with open(filepath, 'r') as original:
        data = original.read()

    with open(filepath, 'w') as new:
        new.write(content + r'\r\n' + data)

def append(filepath, content):
    with open(filepath, 'a') as f:
        f.write(content)

def is_windows():
    return os.name == 'nt'

def get_ec2_conn():
    return boto.ec2.connect_to_region("us-west-2",
        aws_access_key_id=django_settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=django_settings.AWS_SECRET_ACCESS_KEY)


def flatten_reservations(reservations):
    instances = [r.instances for r in reservations]
    chain = itertools.chain(*instances)

    return [i for i in list(chain)]

def get_instances(name):
    ec2 = get_ec2_conn()
    res = ec2.get_all_instances(filters={
        'tag:Name': name
    })

    # we only want running instances
    return [i for i in flatten_reservations(res) if i.state in ['running', 'pending']]


def get_celery_workers(cluster_type):
    """Gets Celery workers belonging to specified cluster type"""
    ec2 = get_ec2_conn()
    res = ec2.get_all_instances(filters={
        'tag:Name': 'CeleryWorkerNG',
        'tag:ClusterType': cluster_type
    })

    # we only want running instances
    return [i for i in flatten_reservations(res) if i.state in ['running', 'pending']]


def launch_celery_worker(cluster_type, branch):
    """Launches a new celery worker, adding it to an appropriate cluster"""
    ec2 = get_ec2_conn()

    # our celery worker AMI
    ami_id = 'ami-d6432ee6'

    reservations = ec2.run_instances(
        ami_id,
        key_name='willet-generic',
        instance_type='t1.micro',
        security_groups=['CeleryWorkers']
    )

    launched_instance = reservations.instances[0]

    print green("Waiting for new instance to startup...")

    # give it some time to become available to API requests
    time.sleep(5)

    status = launched_instance.update()
    while status == 'pending':
        time.sleep(5)
        status = launched_instance.update()

    if status == "running":
        print green("Instance is running. Tagging it...")
        ec2.create_tags([launched_instance.id], {
            "Name": "CeleryWorkerNG",
            "ClusterType": cluster_type
        })

        # with settings(hide('stdout', 'commands')):
        # execute(execute_importer, branch, hosts=[launched_instance.public_dns_name])
        print yellow("Not launching celery bootstrap for branch '{0}' at this point, as it's being buggy.".format(branch))

        print green("Finalized new celery instance: {0}".format(
            launched_instance.id))

    else:
        print red("New instance {0} is not running. Its status: {1}".format(launched_instance.id, status))

    return launched_instance.public_dns_name


def stop_celery_services():
    """Stops celery services and waits until they're confirmed stopped"""
    print green("Waiting for worker services to stop...")
    # run until confirmed
    result = run("/etc/init.d/supervisord stop")
    if "could not find config file" in result:
        print green("Doesn't seem like celery was deployed onto this instance. Skipping.")
        return

    # wait until supervisord is definitely not running
    result = run("/etc/init.d/supervisord status")
    while not "no such file" in result:
        result = run("/etc/init.d/supervisord status")

def start_celery_services(cluster_type):
    """Starts celery services and waits until they're confirmed running"""
    print green("Starting worker services...")
    run("/etc/init.d/supervisord start {0}".format(cluster_type))

    # wait until supervisord started celery worker and/or beat
    result = run("/etc/init.d/supervisord status")
    while "STARTING" in result:
        result = run("/etc/init.d/supervisord status")

def celery_cluster_size(cluster_type, number_of_instances=None, branch='master'):
    """Manages celery cluster of type `cluster_type`.
    Usage:
    Get cluster size: celery_cluster_size(type_name)
    Set number of instances and deploy master branch onto them:
    celery_cluster_size(type_name, number_of_instances=5, branch='master')

    Type options: test or production.
    """
    celery_workers = get_celery_workers(cluster_type)

    current_size = len(celery_workers)
    if number_of_instances:
        number_of_instances = int(number_of_instances)

    print green("'{0}' celery cluster size: {1}".format(
        cluster_type, current_size))
    print green("'{0}' cluster instances: {1}".format(
        cluster_type, [i.public_dns_name for i in celery_workers]))

    if number_of_instances and number_of_instances != current_size or number_of_instances == 0:
        print green("Adjusting cluster size to {0}".format(
            number_of_instances, branch))

        if number_of_instances > current_size:
            public_dns_names = []
            for i in range(number_of_instances - current_size):
                new_dns = launch_celery_worker(cluster_type, branch)
                public_dns_names.append(new_dns)

            # env.user is ignored w/ hosts passed in from CLI, so add it in
            public_dns_names = ["ec2-user@{0}".format(i) for i in
                                public_dns_names]
            public_dns_names = ";".join(public_dns_names)

            print yellow('Now run the following: fab execute_importer:{0},{1},hosts="{2}"'.format(
                cluster_type, branch, public_dns_names))

        else:
            workers_to_terminate = celery_workers[:current_size - number_of_instances]
            workers_dns = [i.public_dns_name for i in workers_to_terminate]

            with settings(hide('stdout', 'commands')):
                execute(stop_celery_services, hosts=workers_dns)

            print green("Terminating instances...")
            ec2 = get_ec2_conn()
            ec2.terminate_instances(
                instance_ids=[i.id for i in workers_to_terminate])

        print green("Finished adjusting celery cluster size to {0}".format(
            number_of_instances))

def deploy_celery(cluster_type, branch):
    """Deploys new code to celery workers and restarts them"""
    print
    # we only support two cluster types
    # (since their names are linked to our environmental vars on workers
    supported_cluster_types = ["test", "production"]
    if cluster_type not in supported_cluster_types:
        print red("Received cluster type: {0}. It must be one of: {1}".format(
            cluster_type, supported_cluster_types))

    print green("Deploying '{0}' to celery worker in {1} cluster".format(
        branch, cluster_type))

    env_path = "/home/ec2-user/pinpoint/env"
    project_path = "{0}/SecondFunnel".format(env_path)
    git_path = "ssh://git@github.com/Willet/SecondFunnel.git"

    print green("Pulling latest code")
    with cd(env_path):
        with settings(hide('warnings'), warn_only=True):
            run("git clone {0}".format(git_path))

    with cd(project_path):
        run("git fetch")
        run("git checkout {0}".format(branch))
        run("git pull".format(branch))

        print green("Updating SSH keys")
        run("cat ./ssh_keys > /home/ec2-user/.ssh/authorized_keys")

        print green("Installing required libraries")
        run("source ../bin/activate && pip install -r requirements.txt")

        print green("Configuring supervisord")
        sudo("cp scripts/celeryconf/supervisord.initd /etc/init.d/supervisord")
        sudo("chown root:root /etc/init.d/supervisord")
        sudo("chmod 0755 /etc/init.d/supervisord")

    stop_celery_services()
    start_celery_services(cluster_type)

    print green("Success! Celery worker is running latest code from '{0}'"
    .format(branch))


def deploy(cluster_type='test', branch='master'):
    """Runs all of our deployment tasks"""

    print green("Obtaining a list of celery workers...")

    celery_workers = get_celery_workers(cluster_type)
    celery_workers_dns = [i.public_dns_name for i in celery_workers]

    print yellow("Celery Worker instances: {0}".format(celery_workers_dns))

    with settings(hide('stdout', 'commands')):
        execute(deploy_celery, cluster_type, branch, hosts=celery_workers_dns)


def importer(*args, **kwargs):
    """Alias for fabfile"""
    return real_importer(*args, **kwargs)


def scraper(*args, **kwargs):
    """Alias for fabfile"""
    return real_scraper(*args, **kwargs)


def get_postgres_arguments():
    environment_type = os.getenv('PARAM1', '').upper() or 'DEV'

    django.settings_module(
        'secondfunnel.settings.{0}'.format(environment_type.lower())
    )
    from django.conf import settings

    password = 'export PGPASSWORD="{}"'.format(
        settings.DATABASES['default']['PASSWORD']
    )

    arguments = '--host=%s --port=%s --username=%s %s' % (
            settings.DATABASES['default']['HOST'],
            settings.DATABASES['default']['PORT'],
            settings.DATABASES['default']['USER'],
            settings.DATABASES['default']['NAME']
        )

    if is_windows():
        password = ''
        arguments = '-W ' + arguments

    return {
        'password': password,
        'arguments': arguments
    }

def load_database_postgres(path='db.sql'):
    args = get_postgres_arguments()
    arguments = args['arguments']
    password = args['password']

    if password:
        command = '{} && psql -f {} {}'.format(
            password, path, arguments,
        )
    else:
        command = 'psql -f {} {}'.format(
            path, arguments,
        )

    local(command)

def dump_database_postgres(path='/tmp/db.sql'):
    args = get_postgres_arguments()
    arguments = args['arguments']
    password = args['password']

    if password:
        command = '{} && pg_dump ' \
            '--data-only ' \
            '{} > {}'.format(
            password, arguments, path
        )
    else:
        command = 'pg_dump ' \
            '--data-only ' \
            '{} > {}'.format(
            arguments, path
        )

    local(command)

    # Disabling constraints:
    # http://www.openscope.net/2012/08/23/subverting-foreign-key-constraints-in-postgres-or-mysql/

    # Appending to beginning and end of file:
    # http://unix.stackexchange.com/a/65514
    local('fab prepend:'
        'filepath={},content="begin; SET CONSTRAINTS ALL DEFERRED;"'
        .format(path)
    )
    local('fab append:'
        'filepath={},content="commit;"'
        .format(path)
    )

def flush_database_postgres():
    args = get_postgres_arguments()
    arguments = args['arguments']
    password = args['password']

    if password:
        command = '{} && psql -f scripts/flush.sql {}'.format(
            password, arguments
        )
    else:
        command = 'psql -f scripts/flush.sql {}'.format(
            arguments
        )

    local(command)

def production():
    env.hosts = [i.public_dns_name for i in get_instances('tng-master2')][-1:]

def test():
    env.hosts = [i.public_dns_name for i in get_instances('tng-test2')][-1:]

# TODO: Should probably check that psql and pg_dump versions are compatible
def to_local_database(native=True):
    # We assume that by SSH'ing in, we are in the right environment and path

    # More details on Django integration here:
    # http://docs.fabfile.org/en/1.6/api/contrib/django.html

    if not native:
        pass # Error; not implemented

    now = datetime.now()
    str_now = now.strftime('%Y-%m-%dT%H:%M.sql')

    # Dump our local database to backup, then flush it out
    local('fab dump_database_postgres:{}'.format(str_now))
    # ./manage.py flush does not do what you might expect...
    local('python manage.py sqlflush > scripts/flush.sql')
    local('fab flush_database_postgres')

    # Dump the remote database
    run('fab dump_database_postgres')
    get('/tmp/db.sql', 'db.sql')

    # Finally, load the data
    local('fab load_database_postgres')
