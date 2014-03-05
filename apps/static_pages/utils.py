from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.test import RequestFactory
from django.utils.importlib import import_module


def get_bucket_name(bucket_name):
    """
    Generates a bucket name based on current environment.
    """

    if settings.ENVIRONMENT in ["test", "dev"]:
        str_format = '{0}-{1}.secondfunnel.com'
        return str_format.format(settings.ENVIRONMENT, bucket_name)

    elif settings.ENVIRONMENT == "production":
        str_format = '{0}.secondfunnel.com'
        return str_format.format(bucket_name)

    else:
        raise Exception("Unknown ENVIRONMENT name: {0}".format(
            settings.ENVIRONMENT))


def create_dummy_request():
    # Monkeypatch request
    # https://code.djangoproject.com/ticket/15736?cversion=0&cnum_hist=1
    def request(self, **request):
        "Construct a generic request object."
        req = WSGIRequest(self._base_environ(**request))
        req.session = self._session()
        return req

    def _session(self):
        """
        Obtains the current session variables.
        """
        if 'django.contrib.sessions' in settings.INSTALLED_APPS:
            engine = import_module(settings.SESSION_ENGINE)
            cookie = self.cookies.get(settings.SESSION_COOKIE_NAME, None)
            if cookie:
                return engine.SessionStore(cookie.value)
        return {}

    RequestFactory._session = _session
    RequestFactory.request = request

    return RequestFactory().get('/')
