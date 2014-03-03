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
