import sys

from fabric.api import run, cd, execute, settings, env, sudo, hide, task
from fabric.colors import green, yellow, red
from fabric.contrib.files import exists

from aws.api import get_ec2_connection
from aws.utils import flatten_reservations

def get_workers(cluster_type):
    """Gets Celery workers belonging to specified cluster type"""
    ec2 = get_ec2_connection()
    res = ec2.get_all_instances(filters={
        'tag:Name': 'CeleryWorker',
        'tag:ClusterType': cluster_type
    })

    # we only want running instances
    return [i for i in flatten_reservations(res) if i.state in ['running', 'pending']]


@task
def launch_worker(cluster_type="test", branch="master"):
    """Launches a new celery worker, adding it to an appropriate cluster"""
    ec2 = get_ec2_connection()

    # our celery worker AMI
    ami_id = 'ami-e7d1e7d7'

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
            "Name": "CeleryWorker",
            "ClusterType": cluster_type
        })

        # with settings(hide('stdout', 'commands')):
        # execute(execute_importer, branch, hosts=[launched_instance.public_dns_name])
        print yellow("Not launching celery bootstrap for branch '{0}'"
                     " at this point, as it's being buggy.".format(branch))

        print green("Finalized new celery instance: {0}".format(
            launched_instance.id))

    else:
        print red("New instance {0} is not running. Its status: {1}".format(launched_instance.id, status))

    return launched_instance.public_dns_name


@task
def stop_services():
    """Stops celery services and waits until they're confirmed stopped"""
    print green("Waiting for worker services to stop...")
    # run until confirmed
    result = run("/etc/init.d/supervisord stop")
    if "could not find config file" in result:
        print green("Doesn't seem like celery was deployed onto this instance. Skipping.")
        return

    # wait until supervisord is definitely not running
    result = run("/etc/init.d/supervisord status")
    while "no such file" not in result:
        result = run("/etc/init.d/supervisord status")


@task
def start_services(cluster_type):
    """Starts celery services and waits until they're confirmed running"""
    print green("Starting worker services...")
    run("/etc/init.d/supervisord start {0}".format(cluster_type))

    # wait until supervisord started celery worker and/or beat
    result = run("/etc/init.d/supervisord status")
    while "STARTING" in result:
        result = run("/etc/init.d/supervisord status")


@task
def cluster_size(cluster_type, number_of_instances=None, branch='master'):
    """Manages celery cluster of type `cluster_type`.
    Usage:
    Get cluster size: cluster_size(type_name)
    Set number of instances and deploy master branch onto them:
    cluster_size(type_name, number_of_instances=5, branch='master')

    Type options: test or production.
    """
    workers = get_workers(cluster_type)

    current_size = len(workers)
    if number_of_instances:
        number_of_instances = int(number_of_instances)

    print green("'{0}' celery cluster size: {1}".format(
        cluster_type, current_size))
    print green("'{0}' cluster instances: {1}".format(
        cluster_type, [i.public_dns_name for i in workers]))

    if number_of_instances and number_of_instances != current_size or number_of_instances == 0:
        print green("Adjusting cluster size to {0}".format(
            number_of_instances, branch))

        if number_of_instances > current_size:
            public_dns_names = []
            for i in range(number_of_instances - current_size):
                new_dns = launch_worker(cluster_type, branch)
                public_dns_names.append(new_dns)

            # env.user is ignored w/ hosts passed in from CLI, so add it in
            public_dns_names = ["ec2-user@{0}".format(i) for i in
                                public_dns_names]
            public_dns_names = ";".join(public_dns_names)

            print yellow('Now run the following: fab execute_importer:{0},{1},hosts="{2}"'.format(
                cluster_type, branch, public_dns_names))

        else:
            workers_to_terminate = workers[:current_size - number_of_instances]
            workers_dns = [i.public_dns_name for i in workers_to_terminate]

            with settings(hide('stdout', 'commands')):
                execute(stop_services, hosts=workers_dns)

            print green("Terminating instances...")
            ec2 = get_ec2_connection()
            ec2.terminate_instances(
                instance_ids=[i.id for i in workers_to_terminate])

        print green("Finished adjusting celery cluster size to {0}".format(
            number_of_instances))


@task
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

    env_path = "/home/ec2-user"
    project_path = "{0}/SecondFunnel".format(env_path)
    key_path = "{0}/ansible/roles/common/files/public_keys".format(project_path)
    git_path = "ssh://git@github.com/Willet/SecondFunnel.git"

    print green("Pulling latest code")

    if not exists(project_path, verbose=True):
        print green("Cloning repository")
        with cd(env_path):
            run("git clone {0}".format(git_path), stdout=sys.stdout, stderr=sys.stderr)

    with cd(project_path):
        print green("Fetching changes")
        run("git fetch")
        run("git checkout {0}".format(branch))
        run("git pull".format(branch))

        print green("Updating SSH keys")
        pubs = run('ls {0}'.format(key_path))
        pub_files = pubs.split()
        for p in pub_files:
            run("cat {0}/{1} >> /home/ec2-user/.ssh/authorized_keys".format(key_path,p))

        print green("Installing required libraries")
        sudo("pip install -r requirements.txt")

        print green("Configuring supervisord")
        sudo("cp scripts/celeryconf/supervisord.initd /etc/init.d/supervisord")
        sudo("chown root:root /etc/init.d/supervisord")
        sudo("chmod 0755 /etc/init.d/supervisord")

    stop_services()
    start_services(cluster_type)

    print green("Success! Celery worker is running latest code from '{0}'".format(branch))
