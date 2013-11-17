import json
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import httplib2

# http://stackoverflow.com/questions/2217445/django-ajax-proxy-view

# Nick is not a security expert.
# He does, however, recommend we read up security policy to see if using
# CORS is sufficient to prevent against CSRF, because he is having a hard time
# handling that...
@never_cache
@csrf_exempt
def proxy(request, path, base_url=None, raw=False):
    # Normally, we would use the login_required decorator, but it will
    # redirect on fail. Instead, just do the check manually; side benefit: we
    # can also return something more useful
    if not request.user or (request.user and not request.user.is_authenticated()):
        return HttpResponse(
            content='{"error": "Not logged in"}',
            content_type='application/json',
            status=401
        )

    if not base_url:
        url = path
    else:
        url = '%s/%s' % (base_url, path)

    if request.META.get('QUERY_STRING', False):
        url += '?' + request.META['QUERY_STRING']

    # There's probably a more pythonic way to do this, but I feel like it would
    # be ugly
    headers = {}
    for key, value in request.META.iteritems():
        if key.startswith('CONTENT'):
            headers[key] = value
        elif key.startswith('HTTP'):
            headers[key[5:]] = value

    if not headers.get('ApiKey', None):
        headers['ApiKey'] = 'secretword'

    h = httplib2.Http()
    response, content = h.request(
        url,
        method=request.method,
        body=request.body or None,
        headers=headers
    )

    if raw:
        return (response, content)
    else:
        return HttpResponse(
            content=content,
            status=response['status'],
            content_type=response['content-type']
        )


def json_response(data, callback=None, status=200):
    """
    This function now serves JSON as well as JSONP, when callback_name is None.

    @param result   a json-serializable object, or an object that
                    has a json() method.
    @param callback_name  a callback. if omitted, json.
                                      if '', 'callback'.
    """
    def serialize(result):
        response_text = ''

        if isinstance(result, (bool, int, float, str, basestring)):
            response_text = json.dumps(result)
        elif isinstance(result, (tuple, list)):
            result_list = []
            for r in result:
                result_list.append(json.loads(serialize(r)))
            response_text = json.dumps(result_list)
        elif isinstance(result, dict):
            result_list = {}
            for r in result:
                result_list[r] = json.loads(serialize(result[r]))
            response_text = json.dumps(result_list)
        else:
            try:
                response_text = json.dumps(result)
            except TypeError:
                raise # no serialization method worked
        return response_text

    response_text = serialize(data)

    if callback == '':
        callback = 'callback'

    if callback:
        return HttpResponse("{0}({1});".format(callback, response_text),
                            mimetype='application/javascript', status=status)
    else:
        return HttpResponse(response_text,
                            mimetype='application/json', status=status)