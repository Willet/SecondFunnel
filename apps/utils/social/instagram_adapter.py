from instagram import InstagramAPI
from apps.utils.social.utils import Social

class Instagram(Social):
    def __init__(self, *args, **kwargs):
        super(Instagram, self).__init__(*args, **kwargs)

        self._api = InstagramAPI(access_token=self.access_token)

    def _fetch_media(self, **kwargs):
        generator = self._api.user_recent_media(count=5, as_generator=True)

        for results, _ in generator:
            for result in results:
                yield result

    def normalize(self, content):
        # TODO: Check if content is provided
        image = content.images.get('standard_resolution')
        image_url = getattr(image, 'url', None)

        caption = content.caption
        caption_text = getattr(caption, 'text', None)

        return {
            'original_id': content.id,
            'type': 'instagram',
            'text_content': caption_text,
            'image_url': image_url
        }