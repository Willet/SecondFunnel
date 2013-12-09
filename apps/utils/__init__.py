__author__ = 'Nicholas Terwoord'


def noop(*args, **kwargs):
    return None


def proxy(thingy):
    return thingy


def where(lst, **kwargs):
    """Like _.where, returns a list of dicts in the list whose properties
    are the same as the key-val pairs you specify.

    """
    items = []
    this_object_is_bad = False

    for dct in lst:
        for key, val in kwargs.iteritems():
            try:
                if dct[key] != val:
                    this_object_is_bad = True
                    break  # not a qualifying dict
            except KeyError as err:
                this_object_is_bad = True
        if not this_object_is_bad:
            items.append(dct)

    return items
