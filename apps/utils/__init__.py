__author__ = 'Nicholas Terwoord'


def noop(*args, **kwargs):
    return None


def proxy(thingy):
    return thingy


def unique_list(lst):
    return list(set(lst))
