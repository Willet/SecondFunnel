from functools import wraps

from django.core.exceptions import PermissionDenied

from apps.assets.models import Store


def belongs_to_store(view_func):
    """
    Decorator for views accessible by store staff memders.
    Checks that currently logged in user belongs to a list of staff members.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """
        Store could be passed to the view as a model instance or via ID.
        """
        try:
            store_id = kwargs['store_id']
            store = Store.objects.get(pk=store_id)
        except (KeyError, Store.DoesNotExist):
            try:
                if isinstance(args[0], Store):
                    store = args[0]
                else:
                    raise ValueError(
                        "First argument must be either Store instance or store_id")

            except IndexError:
                raise ValueError("Store instance or store_id must be present")

        if not request.user in store.staff.all():
            raise PermissionDenied

        return view_func(request, *args, **kwargs)

    return wrapper

def has_store_feature(*features):
    """Decorator for views that are only accessible if features enabled"""
    def decorator(view_func):
        @wraps(view_func)
        def inner(request, *args, **kwargs):

            try:
                # Assume args[0] exists and is a store instance
                store_id = kwargs.get('store_id')
                if not store_id:
                    store_id = args[0].id
                store = Store.objects.get(pk=store_id)
            except IndexError:
                raise ValueError("Store instance or store_id must be present")
            except AttributeError:
                raise ValueError("First argument must be either Store instance or store_id")
            except Store.DoesNotExist:
                raise ValueError("Store does not exist")

            feature_list = store.features_list()
            if not all(x in feature_list for x in features):
                raise PermissionDenied('Requires feature(s) {0}'.format(features))

            return view_func(request, *args, **kwargs)
        return inner
    return decorator