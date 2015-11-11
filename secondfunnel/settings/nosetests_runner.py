"""
Creates a disposable database for running tests.

(venv) python ./manage.py test --settings=secondfunnel.settings.nosetests_runner -v 2
"""


from dev import *

# Make tests faster
SOUTH_TESTS_MIGRATE = False

# Use db port 5432 to avoid pgbouncer, otherwise can't connect to DB
DATABASES['default']['NAME'] = 'sfdb'
DATABASES['default']['HOST'] = 'localhost'
DATABASES['default']['PORT'] = 5432