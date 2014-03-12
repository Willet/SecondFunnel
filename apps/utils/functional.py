import cPickle

from functools import partial


def noop(*args, **kwargs):
    return None


def proxy(thingy):
    return thingy


def check_keys_exist(dct, keys):
    """Returns true if all keys exist in the dict dct."""
    return all(item in dct for item in keys)


def check_other_keys_dont_exist(dct, keys):
    """Returns true if no other keys exist in the dictionary, other than
    the ones specified by the keys variable.

    this function returns true if the dict is missing those keys (because
    it is still true that other keys don't exist).
    """
    dct_key_set = set(dct.keys())
    key_set = set(keys)
    return len(list(dct_key_set - key_set)) == 0


def where(lst, **kwargs):
    """Like _.where, returns a list of dicts in the list whose properties
    are the same as the key-val pairs you specify.

    """
    def check_keys_and_values(dct, keys):
        return all(item in dct.iteritems() for item in keys)

    check_kwargs = partial(check_keys_and_values, keys=kwargs.iteritems())

    return filter(check_kwargs, lst)


def memoize(function, limit=None):
    """Function memoizing decorator http://code.activestate.com/recipes/496879

    @memoize(100) Will cache up to 100 items, dropping the least recently
                  used if the limit is exceeded.
    @memoize      Same as above, but with no limit on cache size
    """
    if isinstance(function, int):
        def memoize_wrapper(f):
            return memoize(f, function)

        return memoize_wrapper

    dict = {}
    list = []
    def memoize_wrapper(*args, **kwargs):
        key = cPickle.dumps((args, kwargs))
        try:
            list.append(list.pop(list.index(key)))
        except ValueError:
            dict[key] = function(*args, **kwargs)
            list.append(key)
            if limit is not None and len(list) > limit:
                del dict[list.pop(0)]

        return dict[key]

    memoize_wrapper._memoize_dict = dict
    memoize_wrapper._memoize_list = list
    memoize_wrapper._memoize_limit = limit
    memoize_wrapper._memoize_origfunc = function
    memoize_wrapper.func_name = function.func_name
    return memoize_wrapper


def async(fn):
    """Decorated function fn will be run asynchronously.

    Copied (and untested) from
    http://code.activestate.com/recipes/576684-simple-threading-decorator/

    Examples::
    >>> @async
    >>> def task1():
    >>>     pass  # do_something
    >>>
    >>> @async
    >>> def task2():
    >>>     pass  # do_something_too
    >>>
    >>> t1 = task1()
    >>> t2 = task2()
    >>>
    >>> t1.join()
    >>> t2.join()

    :returns Thread object
    """
    from threading import Thread
    from functools import wraps

    @wraps(fn)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=fn, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func
