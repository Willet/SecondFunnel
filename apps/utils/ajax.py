from django.http import HttpResponse

import json


def ajax_response(obj):
    """
    Returns a given ajax object as an HttpResponse

    @param obj: The json object to return.

    @return: An HttpRespose containing the given json object.
    """
    return HttpResponse(json.dumps(obj), mimetype="application/json")


def ajax_success(data=None):
    """
    Returns an ajax object with success set to true.

    @param data: The json object to return.

    @return: An HttpResponse containing the given object and
    success set to true.
    """
    if not data:
        data = {}

    data['success'] = True
    return ajax_response(data)


def ajax_error(data=None):
    """
    Returns an ajax objecu with success set to false.

    @param data: The json object to return.

    @return: An HttpResponse containing the given object and
    success set to false.
    """
    if not data:
        data = {}

    data['success'] = False
    return ajax_response(data)
