from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized


class UserObjectsReadOnlyAuthorization(ReadOnlyAuthorization):
    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        if bundle.request.user and bundle.request.user.id:
            results = object_list.filter(id=bundle.request.user.id)
        else:
            results = []

        return results

    def read_detail(self, object_list, bundle):
        # Is the requested object owned by the user?
        if bundle.request.user and bundle.request.user.id:
            result = (bundle.obj.id == bundle.request.user.id)
        else:
            raise Unauthorized()

        return result