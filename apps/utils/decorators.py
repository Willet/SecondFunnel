import cPickle

from threading import Thread
from functools import wraps

from django.views.decorators.cache import patch_cache_control


def never_ever_cache(decorated_function):
    """Like Django @never_cache but sets more valid cache disabling headers.

    @never_cache only sets Cache-Control:max-age=0 which is not
    enough. For example, with max-axe=0 Firefox returns cached results
    of GET calls when it is restarted.

    http://stackoverflow.com/questions/2095520
    """
    @wraps(decorated_function)
    def wrapper(*args, **kwargs):
        response = decorated_function(*args, **kwargs)
        patch_cache_control(
            response, no_cache=True, no_store=True, must_revalidate=True,
            max_age=0)
        return response
    return wrapper


def returns_unicode(fn, encoding='utf-8'):
    """Decorated function return will always be converted to unicode."""
    @wraps(fn)
    def unicode_func(*args, **kwargs):
        rtn = fn(*args, **kwargs)
        try:
            if isinstance(rtn, unicode):
                return rtn
            else:
                #noinspection PyArgumentList
                return unicode(rtn, encoding)
        except (TypeError, UnicodeDecodeError):
            # not a string / already unicode
            return rtn

    return unicode_func
