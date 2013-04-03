from instagram import InstagramAPI


class Social(object):
    def __init__(self, *args, **kwargs):
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


class Instagram(Social):
    def __init__(self, *args, **kwargs):
        tokens = kwargs.get('tokens')
        if tokens:
            self.access_token = tokens.get('access_token')

        super(Instagram, self).__init__(*args, **kwargs)

        self._api = InstagramAPI(access_token=self.access_token)

    def _fetch_media(self, **kwargs):
        generator = self._api.user_recent_media(as_generator=True, **kwargs)

        for results, _ in generator:
            for result in results:
                yield result

    def normalize(self, content):
        # TODO: Check if content is provided
        image = content.images.get('standard_resolution')
        image_url = getattr(image, 'url', '')

        caption = content.caption
        caption_text = getattr(caption, 'text', '')

        return {
            'type': 'instagram',
            'original_id': content.id,
            'original_url': content.link,
            'text_content': caption_text,
            'image_url': image_url,
            'likes': content.like_count,
            'username': content.user.username,
            'user-image': content.user.profile_picture
        }

class Tumblr(Social):
    def __init__(self, *args, **kwargs):
        tokens = kwargs.get('tokens')
        if tokens:
            self.access_token = tokens.get('oauth_token')

        super(Tumblr, self).__init__(*args, **kwargs)

        # self._api = InstagramAPI(access_token=self.access_token)

    def _fetch_media(self, **kwargs):
        return []

    def normalize(self, content):
        return {
            'type': 'tumblr',
            'original_id': '',
            'original_url': '',
            'text_content': '',
            'image_url': '',
            'likes': '',
            'username': '',
            'user-image': ''
        }