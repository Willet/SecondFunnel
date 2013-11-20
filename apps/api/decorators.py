from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

def check_login(fn):
    """wrap the function around three wrappers that check for custom login."""
    @never_cache
    @csrf_exempt
    def wrapped(*args, **kwargs):
        request = args[0]

        # Normally, we would use the login_required decorator, but it will
        # redirect on fail. Instead, just do the check manually; side benefit: we
        # can also return something more useful
        if not request.user or (request.user and not request.user.is_authenticated()):
            return HttpResponse(
                content='{"error": "Not logged in"}',
                mimetype='application/json',
                status=401
            )

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
