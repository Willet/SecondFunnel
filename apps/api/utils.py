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