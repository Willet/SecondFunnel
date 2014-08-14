import os

from datetime import datetime

from fabric.operations import get, local, run
from fabric.api import task, env, hide
from fabric.contrib import django


@task
def remote_to_local(native=True):
    """
    Copy database to local machine
    """
    # We assume that by SSH'ing in, we are in the right environment and path

    # More details on Django integration here:
    # http://docs.fabfile.org/en/1.6/api/contrib/django.html

    if not native:
        pass  # Error; not implemented

    # Dump the remote database
    file_name = 'db.dump'
    file_path = '/tmp/' + file_name
    dump(file_path)
    get(file_path, file_name)

    restore_local_from_file(path=file_name)


@task
def restore_local_from_file(path="db.dump"):
    """ Drops local database, and restores data from file """
    # make it look like a local only command
    env.hosts = []
    django.settings_module('secondfunnel.settings.dev')
    from django.conf import settings
    # Dump our local database to backup, then flush it out
    now = datetime.now()
    local('fab database.dump:path=%s' % (now.strftime('%Y-%m-%dT%H:%M.dump')))
    # clear all existing data from database
    flush_local()
    # load downloaded database
    local_restore(path=path)


@task
def flush_local():
    """ flush the local machines database """
    old_environment = env.environment
    old_env_hosts = env.hosts
    env.environment = 'DEV'
    env.hosts = []

    args = get_arguments()
    arguments = args['arguments']
    password = args['password']
    command = 'python manage.py sqlflush | psql {}'.format(arguments)
    if password:
        command = '{} && '.format(password) + command
    local(command)

    env.hosts = old_env_hosts
    env.environment = old_environment


def is_windows():
    return os.name == 'nt'


def read_remote_env():
    from fabric.api import settings
    if env.hosts:
        ret = {}
        with hide('output', 'running', 'warnings'), settings(warn_only=True):
            environment = run("env")
            for line in environment.split('\r\n'):
                key, val = line.split('=', 1)
                ret[key] = val
    else:
        ret = os.environ

    return ret


def get_arguments():
    """ parse arguments passed to postgres command """
    django.settings_module(
        'secondfunnel.settings.{0}'.format(env.environment.lower())
    )
    from django.conf import settings

    # workaround for running all from locally, to remote machines
    # but still reading the os environment variables
    # if there is hosts of course
    env.remote_environ = read_remote_env()
    if env.hosts and 'RDS_DB_NAME' in env.remote_environ:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': env.remote_environ['RDS_DB_NAME'],
                'USER': env.remote_environ['RDS_USERNAME'],
                'PASSWORD': env.remote_environ['RDS_PASSWORD'],
                'HOST': env.remote_environ['RDS_HOSTNAME'],
                'PORT': env.remote_environ['RDS_PORT'],
                }
        }
    else:
        DATABASES = settings.DATABASES

    password = 'export PGPASSWORD="{}"'.format(
        DATABASES['default']['PASSWORD']
    )

    arguments = '--host=%s --port=%s --username=%s --dbname=%s' % (
        DATABASES['default']['HOST'],
        DATABASES['default']['PORT'],
        DATABASES['default']['USER'],
        DATABASES['default']['NAME']
        )

    if is_windows():
        password = ''
        arguments = '-W ' + arguments

    return {
        'password': password,
        'arguments': arguments,
    }


@task
def dump(path='/tmp/db.dump'):
    """ dump database to --path=/tmp/db.dump """
    args = get_arguments()
    arguments = args['arguments']
    password = args['password']

    command = 'pg_dump --data-only --format=custom {} -f {}'.format(arguments, path)
    if password:
        command = '{} && '.format(password) + command

    # TODO: this always runs local, it should be smarter :(
    if env.hosts:
        run(command)
    else:
        local(command)


@task
def local_restore(path='db.dump'):
    """
    restore database fump dump (--path=db.dump)
    """
    args = get_arguments()
    arguments = args['arguments']
    password = args['password']

    command = 'pg_restore --data-only --format=custom --single-transaction {} {}'.format(
        arguments, path
    )
    if password:
        command = '{} && '.format(password) + command

    # TODO: this always runs local, it should be smarter :(
    local(command)
