from instagram import InstagramAPI
from apps.utils.social.utils import Social

class Instagram(Social):
    def __init__(self, *args, **kwargs):
        super(Instagram, self).__init__(*args, **kwargs)

        self._api = InstagramAPI(access_token=self.access_token)

    def _fetch_media(self, since=None, page=None):
        if since:
            media = []

            # For whatever reason, the generator is really ugly...
            generator = self._api.user_recent_media(as_generator=True)
            for results, _ in generator:
                for result in results:
                    if since < result.created_time:
                        media.append(result)
                    else:
                        return media

            return media
        else:
            results, _ = self._api.user_recent_media()
            return results

    def normalize(self, content):
        # TODO: Check if content is provided
        image = content.images.get('standard_resolution')
        image_url = getattr(image, 'url', None)

        caption = content.caption
        caption_text = getattr(caption, 'text', None)

        return {
            'id': content.id,
            'type': 'instagram',
            'caption': caption_text,
            'image_url': image_url
        }