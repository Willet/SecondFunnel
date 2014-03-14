from functools import wraps
import json

from django.http import HttpResponse

from apps.assets.models import BaseModel


def ajax_jsonp(result, callback_name=None, status=200, request=None):
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
        elif isinstance(result, BaseModel):
            response_text = result.to_json()
        elif isinstance(result, (tuple, list)):
            result_list = []
            for r in result:
                if isinstance(r, BaseModel):
                    result_list.append(r.to_json())
                elif isinstance(r, dict):
                    result_list.append(r)
                else:
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
                raise  # no serialization method worked
        return response_text

    response_text = serialize(result)

    if callback_name == '':
        callback_name = 'callback'

    if callback_name:
        resp = HttpResponse("{0}({1});".format(callback_name, response_text),
                            content_type='application/javascript', status=status)
    else:
        resp = HttpResponse(response_text,
                            content_type='application/json', status=status)

    return resp


def returns_json(callback_name=None):
    """Turns ajax_jsonp into a decorator. fn will become a view that
    returns json.

    @returns_json()
    @returns_json(callback_name='fn')
    # or calling the view with ?callback=whatever
    """
    def dec(fn):

        @wraps(fn)
        def wrapped_view(request, *args, **kwargs):
            _callback_name = callback_name  # TIL python hoisting

            kwargs.update({'request': request})

            if not callback_name and kwargs.get('callback'):
                _callback_name = kwargs.get('callback')

            if not callback_name and request.GET.get('callback'):
                _callback_name = request.GET.get('callback')

            try:
                res = fn(*args, **kwargs)
            except:
                return ajax_jsonp(None, status=500)

            return ajax_jsonp(res, callback_name=_callback_name)

        return wrapped_view
    return dec


def returns_cg_json(fn):
    """Turns ajax_jsonp into a decorator. fn will become a view that
    returns CG-style json.
    """

    @wraps(fn)
    def wrapped_view(request, *args, **kwargs):
        try:
            res = fn(request, *args, **kwargs)
        except:
            return ajax_jsonp({}, status=500)

        return ajax_jsonp({'results': res})

    return wrapped_view
