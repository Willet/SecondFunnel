import json

from django.http import HttpResponse

from apps.assets.models import Product, Store, BaseModel


def ajax_jsonp(result, callback_name=None, status=200, request=None,
               add_cors_headers=False):
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

    # colour me baffled, but the django corsheaders middleware does nothing
    # on elastic beanstalk instances. These lines patch the response object
    # with the request's (if available) origin headers, if settings says so.
    if add_cors_headers and request:
        protocol = 'https://' if request.is_secure() else 'http://'
        resp['Access-Control-Allow-Origin'] = protocol + request.get_host()

    return resp
