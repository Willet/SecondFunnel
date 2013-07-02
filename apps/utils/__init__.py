__author__ = 'Nicholas Terwoord'

def noop(*args, **kwargs):
    return None

def safe_getattr(instance, key, default=None):
    try:
        return getattr(instance, key, default)
    except:
        return default