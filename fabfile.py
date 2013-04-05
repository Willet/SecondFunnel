"""
Automated deployment tasks
"""
from fabric.api import roles, run, cd, execute, settings, env, sudo

env.roledefs = {
    'celery': ['ec2-user@ec2-54-244-159-249.us-west-2.compute.amazonaws.com'],
}

@roles('celery')
def deploy_celery():
    """Deploys new code to celery workers and restarts them"""

    env_path = "/home/ec2-user/pinpoint/env"
    project_path = "/home/ec2-user/pinpoint/env/SecondFunnel"
    git_path = "ssh://git@github.com/Willet/SecondFunnel.git"

    with cd(env_path):
        with settings(warn_only=True):
            run("git clone {}".format(git_path))

    with cd(project_path):
        run("git checkout celeryservices")
        run("git pull origin celeryservices")

        sudo("cp scripts/celeryconf/supervisord.initd /etc/init.d/supervisord")
        sudo("chown root:root /etc/init.d/supervisord")
        sudo("chmod 0755 /etc/init.d/supervisord")

    result = run("/etc/init.d/supervisord stop")
    while not "no such file" in result:
        result = run("/etc/init.d/supervisord stop")

    run("/etc/init.d/supervisord start")

    result = run("/etc/init.d/supervisord status")
    while "STARTING" in result:
        result = run("/etc/init.d/supervisord status")


def deploy():
    """Runs all of our deployment tasks"""
    execute(deploy_celery)
