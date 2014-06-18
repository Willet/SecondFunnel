import os

from datetime import datetime

from fabric.operations import local, get
from fabric.api import run, task
from fabric.contrib import django
from fabfile.os import is_windows


@task
def to_local_database(native=True):
    """
    Copy database to local machine
    """
    # We assume that by SSH'ing in, we are in the right environment and path

    # More details on Django integration here:
    # http://docs.fabfile.org/en/1.6/api/contrib/django.html

    if not native:
        pass  # Error; not implemented

    now = datetime.now()
    str_now = now.strftime('%Y-%m-%dT%H:%M.sql')

    # Dump our local database to backup, then flush it out
    local('fab dump_database:{}'.format(str_now))
    # ./manage.py flush does not do what you might expect...
    local('python manage.py sqlflush > scripts/flush.sql')
    local('fab flush_database')

    # Dump the remote database
    run('fab dump_database')
    get('/tmp/db.dump', 'db.dump')

    # Finally, load the data
    local('fab load_database')


def get_arguments():
    """ parse arguments passed to postgres command """
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


@task
def dump_database(path='/tmp/db.dump'):
    """
    dump database to --path=/tmp/db.dump
    """
    args = get_arguments()
    arguments = args['arguments']
    password = args['password']

    command = 'pg_dump --data-only --format=custom {} -f {}'.format(arguments, path)
    if password:
        command = '{} && '.format(password) + command

    local(command)


@task
def flush_database():
    """
    execute flush  (delete all data, but do not drop tables) script in database.
    """

    args = get_arguments()
    arguments = args['arguments']
    password = args['password']

    command = 'psql -f scripts/flush.sql {}'.format(
        arguments
    )
    if password:
        command = '{} && '.format(password) + command

    local(command)


@task
def load_database(path='db.dump'):
    """
    restore database fump dump (--path=db.dump)
    """
    args = get_arguments()
    arguments = args['arguments']
    password = args['password']

    command = 'pg_restore --data-only --format=custom --single-transaction {} -f {}'.format(
        path, arguments,
    )
    if password:
        command = '{} && '.format(password) + command

    local(command)
