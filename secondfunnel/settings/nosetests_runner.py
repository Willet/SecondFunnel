"""
Creates a disposable database for running tests.

(venv) python ./manage.py test --settings=secondfunnel.settings.nosetests_runner
"""


from dev import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': from_project_root('test.db'),
    }
}
