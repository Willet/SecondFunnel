from fabric.api import task


@task(alias='deploy')
def deploy(cluster_type='test', branch='master'):
    """Runs all of our deployment tasks"""

    print green("Obtaining a list of celery workers...")

    celery_workers = get_celery_workers(cluster_type)
    celery_workers_dns = [i.public_dns_name for i in celery_workers]

    print yellow("Celery Worker instances: {0}".format(celery_workers_dns))

    with settings(hide('stdout', 'commands')):
        execute(deploy_celery, cluster_type, branch, hosts=celery_workers_dns)


