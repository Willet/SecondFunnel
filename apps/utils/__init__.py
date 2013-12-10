__author__ = 'Nicholas Terwoord'


def noop(*args, **kwargs):
    return None


def proxy(thingy):
    return thingy


def where(lst, **kwargs):
    """Like _.where, returns a list of dicts in the list whose properties
    are the same as the key-val pairs you specify.

    """
    def check_keys(dct):
        return all(item in dct.iteritems() for item in kwargs.iteritems())

    return filter(check_keys, lst)
