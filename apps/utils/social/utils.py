import json
from apps.assets.models import Store


class Social(object):
    def __init__(self, *args, **kwargs):
        tokens = kwargs.get('tokens')

        if tokens:
            self.access_token = tokens.get('access_token')

        if not self.access_token:
            raise

    def _fetch_media(self):
        return []

    def get_content(self, **kwargs):
        """Returns a list of content in a standard format."""
        generator = self._fetch_media(**kwargs)

        content = []

        # TODO: Do this more intelligently
        # As it stands, this could take a long time to get all the contents
        for result in generator:
            content.append(self.normalize(result))

        return content

    def normalize(self, content):
        """Converts content from a service into a regular format"""
        return content

        # What common operations will there be?
        #   Access 'content'
        #       What is content? Images? Posts? Etc.
        #       ...Is that it? Really?
        #           Well, we'll need to marshall the content, maybe fetch it offline...


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