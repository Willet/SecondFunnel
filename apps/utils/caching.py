NOCACHE_PARAMS = ['dev', 'no-cache']


def nocache(request):
    """A callable for fancy cache's `key_prefix`

    Will not cache the page if certain GET parameters are present.
    """
    if any(x in request.GET for x in NOCACHE_PARAMS):
        return None

    return ''