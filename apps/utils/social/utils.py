import json


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

"""
is_new = False
new_association=True
backend = { 'name' }
details={'username'}
response['data']
uid
"""

def social_auth_changed(*args, **kwargs):
    instance = kwargs.get('instance')
    created = kwargs.get('created')

    if not (instance and created):
        return

    # Superusers tend to belong to multiple stores; don't associate if so.
    if instance.user.is_superuser:
        return

    stores = Store.objects.filter(staff=instance.user)

    for store in stores:
        store.social_auth.add(instance)
        store.save()


        # post_save.connect(social_auth_changed, sender=UserSocialAuth)