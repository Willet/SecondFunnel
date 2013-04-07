from django.conf import settings
from instagram import InstagramAPI
from tumblpy import Tumblpy


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
            self.secret_token = tokens.get('oauth_token_secret')

        super(Tumblr, self).__init__(*args, **kwargs)

        self._api = Tumblpy(app_key=settings.TUMBLR_CONSUMER_KEY,
                            app_secret=settings.TUMBLR_CONSUMER_SECRET,
                            oauth_token=self.access_token,
                            oauth_token_secret=self.secret_token)

    def _fetch_media(self, **kwargs):
        #TODO: Make generator?
        media = []
        for blog in self._get_blogs():
            # Note: We cannnot supply multiple types
            # In other words. We either get one type,
            # or filter ourselves
            response = self._api.get(
                'posts',
                blog_url=blog.get('url'),
                params={'type': 'photo'}
            )

            posts = response.get('posts')

            # I feel like there's a more susinct way to do this, I just don't
            # know how...
            for post in posts:
                for photo in post['photos']:
                    revised_post = post
                    revised_post['photo'] = photo
                    media.append(revised_post)

        return media

    def _get_blogs(self):
        response = self._api.post('user/info')

        return [blog for blog in response['user']['blogs']]

    def _get_avatar(self, blog):
        blog_url = '{0}.tumblr.com'.format(blog)
        avatar = self._api.get_avatar_url(blog_url=blog_url, size=512)
        return avatar['url']

    def normalize(self, content):
        # Assuming content is a photo
        blog_name = content.get('blog_name')
        avatar = self._get_avatar(blog_name)

        return {
            'type': 'tumblr',
            'original_id': content.get('id'),
            'original_url': content.get('post_url'),
            'text_content': content.get('caption'),
            'image_url': content['photo']['original_size'].get('url'),
            'likes': content.get('note_count'),
            'username': blog_name,
            'user-image': avatar
        }