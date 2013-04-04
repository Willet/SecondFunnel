"""
Automated deployment tasks
"""
from fabric.api import roles, run, cd, execute

env.roledefs = {
    'celery': ['ec2-user@ec2-54-244-159-249.us-west-2.compute.amazonaws.com'],
}

@roles('celery')
def deploy_celery():
    """Deploys new code to celery workers and restarts them"""

    project_dir = "/home/ec2-user/pinpoint/env/SecondFunnel"

    with cd(project_dir):
        run("git checkout celeryservices")
        run("git pull origin celeryservices")

    run("/etc/init.d/supervisord restart")

def deploy():
    """Runs all of our deployment tasks"""
    execute(deploy_celery)
