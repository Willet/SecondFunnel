from apps.assets.models import Store
from apps.utils.social import adapters


def get_adapter_class(classname):
    return getattr(adapters, classname)


def update_social_auth(backend, details, response, social_user, uid, user,
                       *args, **kwargs):
    if getattr(backend, 'name', None) == 'instagram':
        social_user.extra_data['username'] = details.get('username')

    social_user.save()

    associate_user_with_stores(user, social_user)

# TODO: Should this be part of the pipeline?
def associate_user_with_stores(user, social_user):
    # Since superuser is connected to all stores,
    # DON'T associate with stores if superuser
    if user.is_superuser:
        return

    stores = Store.objects.filter(staff=user)

    for store in stores:
        store.social_auth.add(social_user)
        store.save()