# python.net/~goodger/projects/pycon/2007/idiomatic/handout.html#importing
from functools import wraps
import itertools
from threading import current_thread

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


def thread_id(fn):
    """Says "thread started" / "thread ended" before and after a django view
    runs.
    """
    @wraps(fn)
    def func(*args, **kwargs):
        this_thread = current_thread()
        print "{0} started".format(this_thread.name)
        rtn = fn(*args, **kwargs)
        print "{0} ended".format(this_thread.name)
        return rtn

    return func


def flatten(list_of_lists):
    """
    Takes an iterable of iterables, returns a single iterable containing all items
    """
    # todo: test me
    return itertools.chain(*list_of_lists)
