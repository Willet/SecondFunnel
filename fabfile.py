"""
Automated deployment tasks
"""
from fabric.api import roles, run, cd, execute, settings, env, sudo

env.user = 'ec2-user'
env.roledefs = {
    'celery': [
        'ec2-54-244-159-249.us-west-2.compute.amazonaws.com',
        'ec2-54-244-215-223.us-west-2.compute.amazonaws.com',
    ],
}

@roles('celery')
def deploy_celery(branch):
    """Deploys new code to celery workers and restarts them"""

    env_path = "/home/ec2-user/pinpoint/env"
    project_path = "{}/SecondFunnel".format(env_path)
    git_path = "ssh://git@github.com/Willet/SecondFunnel.git"

    with cd(env_path):
        with settings(warn_only=True):
            run("git clone {}".format(git_path))

    with cd(project_path):
        run("git checkout {}".format(branch))
        run("git pull origin {}".format(branch))

        run("source ../bin/activate && pip install -r requirements.txt")

        sudo("cp scripts/celeryconf/supervisord.initd /etc/init.d/supervisord")
        sudo("chown root:root /etc/init.d/supervisord")
        sudo("chmod 0755 /etc/init.d/supervisord")

    # run until confirmed
    run("/etc/init.d/supervisord stop")

    # wait until supervisord is definitely not running
    result = run("/etc/init.d/supervisord status")
    while not "no such file" in result:
        result = run("/etc/init.d/supervisord status")

    run("/etc/init.d/supervisord start")

    # wait until supervisord started celery worker and/or beat
    result = run("/etc/init.d/supervisord status")
    while "STARTING" in result:
        result = run("/etc/init.d/supervisord status")


def deploy(branch='master'):
    """Runs all of our deployment tasks"""
    execute(deploy_celery, branch)
