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
