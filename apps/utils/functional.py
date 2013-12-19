from functools import partial


def noop(*args, **kwargs):
    return None


def proxy(thingy):
    return thingy


def check_keys_exist(dct, keys):
    """Returns true if all keys exist in the dict dct."""
    return all(item in dct for item in keys)


def where(lst, **kwargs):
    """Like _.where, returns a list of dicts in the list whose properties
    are the same as the key-val pairs you specify.

    """
    def check_keys_and_values(dct, keys):
        return all(item in dct.iteritems() for item in keys)

    check_kwargs = partial(check_keys_and_values, keys=kwargs.iteritems())

    return filter(check_kwargs, lst)
