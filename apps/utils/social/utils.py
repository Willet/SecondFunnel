from apps.assets.models import Store
from apps.utils.social import adapters


def get_adapter_class(classname):
    return getattr(adapters, classname, None)


def update_social_auth(backend, details, response, social_user, uid, user,
                       *args, **kwargs):

    # Until the `extra_data` method is fixed for instagram and tumblr
    # (and likely, any other `contrib` backends), need to do this instead
    # of just using *_EXTRA_DATA
    if getattr(backend, 'name', None) in ('instagram', 'tumblr'):
        social_user.extra_data['username'] = details.get('username')

    social_user.save()

    associate_user_with_stores(user, social_user)

# TODO: Separate step in pipeline
def associate_user_with_stores(user, social_user):
    # Since superuser is connected to all stores,
    # DON'T associate with stores if superuser
    if user.is_superuser:
        return

    stores = Store.objects.filter(staff=user)

    for store in stores:
        store.social_auth.add(social_user)
