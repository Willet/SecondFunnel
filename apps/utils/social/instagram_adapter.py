from instagram import InstagramAPI
from apps.utils.social.utils import Social

class Instagram(Social):
    def __init__(self, *args, **kwargs):
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
            'user': {
                'username': content.user.username,
                'image': content.user.profile_picture
            }
        }
