import functools

from django.http import HttpResponse, HttpResponseNotAllowed
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt


def check_login(fn):
    """wrap the function around three wrappers that check for custom login."""
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        request = args[0]

        # Normally, we would use the login_required decorator, but it will
        # redirect on fail. Instead, just do the check manually; side benefit:
        # we can also return something more useful
        if not (request.user and request.user.is_authenticated()):
            return HttpResponse(
                content='{"error": "Not logged in"}',
                mimetype='application/json',
                status=401
            )

        return fn(*args, **kwargs)
    return wrapped


def append_headers(fn):
    """Provide the function's request object with a new NEW_HEADERS
    that the proxy can use to relay.
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        request = args[0]

        # add custom header values
        headers = {}
        for key, value in request.META.iteritems():
            if key.startswith('CONTENT'):
                headers[key] = value
            elif key.startswith('HTTP'):
                headers[key[5:]] = value

        headers.update({'ApiKey': 'secretword'})

        request.NEW_HEADERS = headers

        return fn(*args, **kwargs)
    return wrapped


def request_methods(*request_methods):
    def wrap(func):
        @functools.wraps(func)
        def wrapped_func(request, *args, **kwargs):
            if not request.method in request_methods:
                return HttpResponseNotAllowed(request_methods)
            return func(request, *args, **kwargs)
        # this is returning the decorated function
        return wrapped_func
    # this is returning the decorator
    return wrap
