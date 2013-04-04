"""
Automated deployment tasks
"""
from fabric.api import hosts, run, cd

CELERY_WORKERS = ['ec2-54-244-159-249.us-west-2.compute.amazonaws.com']

@hosts(CELERY_WORKERS)
def deploy_celery():
    """Deploys new code to celery workers and restarts them"""

    project_dir = "/home/ec2-user/pinpoint/env/SecondFunnel"

    with cd(project_dir):
        run("git checkout master")
        run("git pull origin master")

    run("/etc/init.d/supervisord restart")
