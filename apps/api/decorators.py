import functools
import json

from django.http import HttpResponse, HttpResponseNotAllowed
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from apps.utils import check_keys_exist
from apps.utils.functional import check_other_keys_dont_exist
from secondfunnel.errors import MissingRequiredKeysError, TooManyKeysError


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
    """Returns a decorator that returns HTTP 405 if the current request
    was not made with one of the methods specified in request_methods.

    Example: @request_methods('GET')  # raises on anything but GET
    """
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


def validate_json_deserializable(fn):
    """Returns a malformed-json error if the message is not
    json-deserializable.

    This decorator decorator targets SQS queue-processing functions that
    accept one SQS queue message.
    """
    @functools.wraps(fn)
    def wrap(*args, **kwargs):
        msg = args[0]

        try:
            # each message is a page id
            message = json.loads(msg)
        except (TypeError, ValueError) as err:
            # safeguard for "No JSON object could be decoded"
            # def json_err(*args, **kwargs):
            #     return {err.__class__.name: err.message}
            # return json_err
            return {err.__class__.__name__: err.message}

        return fn(*args, **kwargs)
    return wrap


def require_keys_for_message(only_those_keys=True, *keys):
    """Returns a decorator that returns a malformed-message dict and
    the dict at fault, or the function that was meant to be run.

    This decorator decorator targets SQS queue-processing functions that
    accept one SQS queue message.

    :param only_those_keys: throw exception if the message
    contains more keys than the ones you are expecting.

    Example:
    # returns error dict if *args[0]['a'] doesn't exist
    @require_keys_for_message('a')
    """
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped_fn(dct, *args, **kwargs):
            print (dct, keys)  # dct is still a string at this point
                               # (converted to dict next line)
            if not check_keys_exist(dct, keys=keys):
                raise MissingRequiredKeysError(keys)
            if only_those_keys and not check_other_keys_dont_exist(
                    dct, keys=keys):
                raise TooManyKeysError(keys)
            return fn(*((dct, ) + args), **kwargs)
        return wrapped_fn
    return wrap
