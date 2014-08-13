"""
WSGI config for secondfunnel project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secondfunnel.settings.production")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from django.conf import settings
if settings.DEBUG:
    print "loading werkzeug debugger for local application on wsgi"

    # disable the normal 500 response debugger
    from django_extensions.management.technical_response import null_technical_500_response
    from django.views import debug
    debug.technical_500_response = null_technical_500_response

    # wrap the wsgi handler in the werkzeug debugger
    from werkzeug.debug import DebuggedApplication
    application = DebuggedApplication(application, evalex=True)

# CELERY
import djcelery
djcelery.setup_loader()
