# python.net/~goodger/projects/pycon/2007/idiomatic/handout.html#importing
from functools import wraps
from functional import async, check_keys_exist, memoize, noop, proxy, where


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
        except (TypeError, UnicodeDecodeError) as err:
            # not a string / already unicode
            return rtn

    return unicode_func
