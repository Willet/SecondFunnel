"""
Automated deployment tasks
"""
from fabric.api import roles, run, cd, execute, settings, env, sudo, hide
from fabric.colors import green, yellow
from secondfunnel.settings import common as django_settings

import boto.ec2
import itertools

env.user = 'ec2-user'

def get_ec2_conn():
    return boto.ec2.connect_to_region("us-west-2",
        aws_access_key_id=django_settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=django_settings.AWS_SECRET_ACCESS_KEY)

def flatten_reservations(reservations):
    instances = [r.instances for r in reservations]
    chain = itertools.chain(*instances)

    return [i for i in list(chain)]

def get_celery_workers():
    ec2 = get_ec2_conn()
    res = ec2.get_all_instances(filters={'tag:Name': 'CeleryWorker'})

    instances = flatten_reservations(res)
    return [i.public_dns_name for i in instances if i.public_dns_name]

def launch_celery_worker():
    ec2 = get_ec2_conn()

    # our celery worker AMI
    ami_id = 'ami-c00c98f0'

    reservations = ec2.run_instances(
        ami_id,
        key_name='gri-public',
        instance_type='t1.micro',
        security_groups=['CeleryWorkers']
    )

    instance_id = reservations.instances[0].id
    print green("Launched new celery instance: {}".format(instance_id))

    ec2.create_tags([instance_id], {"Name": "CeleryWorker"})

@roles('celery')
def deploy_celery(branch):
    """Deploys new code to celery workers and restarts them"""
    print
    print green("Deploying '{}' to celery worker".format(branch))

    env_path = "/home/ec2-user/pinpoint/env"
    project_path = "{}/SecondFunnel".format(env_path)
    git_path = "ssh://git@github.com/Willet/SecondFunnel.git"

    print green("Pulling latest code")
    with cd(env_path):
        with settings(hide('warnings'), warn_only=True):
            run("git clone {}".format(git_path))

    with cd(project_path):
        run("git checkout {}".format(branch))
        run("git pull origin {}".format(branch))

        print green("Installing required libraries")
        run("source ../bin/activate && pip install -r requirements.txt")

        print green("Configuring supervisord")
        sudo("cp scripts/celeryconf/supervisord.initd /etc/init.d/supervisord")
        sudo("chown root:root /etc/init.d/supervisord")
        sudo("chmod 0755 /etc/init.d/supervisord")

    print green("Waiting for worker services to stop...")
    # run until confirmed
    run("/etc/init.d/supervisord stop")

    # wait until supervisord is definitely not running
    result = run("/etc/init.d/supervisord status")
    while not "no such file" in result:
        result = run("/etc/init.d/supervisord status")

    print green("Starting worker services...")
    run("/etc/init.d/supervisord start")

    # wait until supervisord started celery worker and/or beat
    result = run("/etc/init.d/supervisord status")
    while "STARTING" in result:
        result = run("/etc/init.d/supervisord status")

    print green("Success! Celery worker is running latest code from '{}'".format(branch))


def deploy(branch='master'):
    """Runs all of our deployment tasks"""

    print green("Obtaining a list of celery workers...")

    celery_workers = get_celery_workers()
    print yellow("Celery Worker instances: {}".format(celery_workers))

    with settings(hide('stdout', 'commands')):
        execute(deploy_celery, branch, hosts=celery_workers)
