from instagram import InstagramAPI
from apps.utils.social.utils import Social

class Instagram(Social):
    def __init__(self, *args, **kwargs):
        super(Instagram, self).__init__(*args, **kwargs)

        self._api = InstagramAPI(access_token=self.access_token)

    def _fetch_media(self):
        media, page = self._api.user_recent_media()

        return media

    def normalize(self, content):
        # TODO: Check if content is provided
        image = content.images.get('standard_resolution')
        image_url = getattr(image, 'url', None)

        return {
            'id': content.id,
            'type': 'instagram',
            'caption': content.caption.text,
            'image_url': image_url
        }