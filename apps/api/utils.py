import httplib2
import json
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized


class UserObjectsReadOnlyAuthorization(ReadOnlyAuthorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        try:
            return object_list.filter(id=bundle.request.user.id)
        except:
            return []

    def read_detail(self, object_list, bundle):
        # Is the requested object owned by the user?
        try:
            return (bundle.obj.id == bundle.request.user.id)
        except:
            raise Unauthorized()


def copy_headers_to_response(headers, response):
    for k, v in headers.iteritems():
        if k != 'connection':
            response[k] = v
    return response


def mimic_response(client_response, server_response):
    copy_headers_to_response(client_response.headers, server_response)
    return server_response


def get_proxy_results(request, url, body=None, raw=False, method=None):
    """small wrapper around all api requests to content graph.

    :param raw if True, returns the entire http tuple.
    :type raw bool

    :param method if given, overrides the one in request.
    :type method str

    :returns tuple
    :raises (ValueError, IndexError)
    """
    h = httplib2.Http()
    response, content = h.request(uri=url, method=method or request.method,
        body=body, headers=request.NEW_HEADERS or request.META)

    if raw:
        return (response, content)

    resp_obj = json.loads(content)
    return (resp_obj['results'], resp_obj['meta'])