from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.handlers.wsgi import WSGIRequest
from django.test import RequestFactory
from django.utils.importlib import import_module

from apps.static_pages.models import StaticLog
from apps.assets.models import Store


def save_static_log(object_class, object_id, key):
    object_type = ContentType.objects.get_for_model(object_class)
    log_record = StaticLog(
        content_type=object_type, object_id=object_id, key=key)
    log_record.save()


def remove_static_log(object_class, object_id, key):
    object_type = ContentType.objects.get_for_model(object_class)
    log_records = StaticLog.objects.filter(
        content_type=object_type, object_id=object_id, key=key).delete()


def bucket_exists_or_pending(store):
    store_type = ContentType.objects.get_for_model(Store)

    log_records = StaticLog.objects.filter(
            content_type=store_type, object_id=store.id)

    return len(log_records) > 1


def get_remote_data(*args, **kwargs):
    """Mocked datasource.

    Returns the first positional argument, or, if kwargs are present,
    a dictionary of the kwargs... which is just kwargs.
    """
    return kwargs or args[0] or None


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
