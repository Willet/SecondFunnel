from django.http import HttpResponse

import json


def ajax_response(obj):
    return HttpResponse(json.dumps(obj), mimetype="application/json")

def ajax_success(data=None):
    if not data:
        data = {}

    data['success'] = True
    return ajax_response(data)

def ajax_error(data=None):
    if not data:
        data = {}

    data['success'] = False
    return ajax_response(data)
