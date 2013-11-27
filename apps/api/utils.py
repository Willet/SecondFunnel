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
    for k, v in headers.items():
        if k != 'connection':
            response[k] = v
    return response


def mimic_response(client_response, server_response):
    copy_headers_to_response(client_response.headers, server_response)
    return server_response
