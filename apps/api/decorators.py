import functools
import json

from django.http import HttpResponse, HttpResponseNotAllowed

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
                content_type='application/json',
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
            json.loads(msg)
        except (TypeError, ValueError):
            # give it a name
            raise ValueError("JSON was not deserializable")

        return fn(*args, **kwargs)
    return wrap


def require_keys_for_message(keys, only_those_keys=True):
    """Returns a decorator that returns a malformed-message dict and
    the dict at fault, or the function that was meant to be run.

    This decorator decorator targets SQS queue-processing functions that
    accept one SQS queue message.

    :param only_those_keys: throw exception if the message
    contains more keys than the ones you are expecting.

    Example:
    # returns error dict if *args[0]['a'] doesn't exist
    @require_keys_for_message(['a'])
    """
    def wrap(fn):
        @functools.wraps(fn)
        def wrapped_fn(dct, *args, **kwargs):
            print (dct, keys)  # dct is still a string at this point
                               # (converted to dict next line)
            if not check_keys_exist(dct, keys=keys):
                raise MissingRequiredKeysError(keys)

            if only_those_keys and not check_other_keys_dont_exist(
                    json.loads(dct), keys=keys):
                raise TooManyKeysError(
                    expected=json.loads(dct).keys(),
                    got=keys)
            return fn(*((dct, ) + args), **kwargs)
        return wrapped_fn
    return wrap
