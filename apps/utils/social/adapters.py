from apiclient.discovery import build
import httplib2
from instagram import InstagramAPI
from oauth2client.client import AccessTokenCredentials


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

class Youtube(Social):
    def __init__(self, *args, **kwargs):
        tokens = kwargs.get('tokens')

        if tokens:
            self.access_token = tokens.get('access_token')

        super(Youtube, self).__init__(*args, **kwargs)

        credentials = AccessTokenCredentials(
            self.access_token, 'SecondFunnel/1.0'
        )

        http = httplib2.Http()
        http = credentials.authorize(http)

        self._api = build('youtube', 'v3', http=http)

    def _fetch_media(self, **kwargs):
        # Modified from example:
        # https://developers.google.com/youtube/v3/code_samples/python#my_uploads
        response = self._api.channels().list(
            mine=True,
            part="contentDetails"
        ).execute()

        media = []
        for channel in response['items']:
            uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

            next_page_token = ''
            while next_page_token is not None:
                item_response = self._api.playlistItems().list(
                    playlistId=uploads_list_id,
                    part="snippet",
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()

                media.extend(item['snippet'] for item in item_response['items'])

                next_page_token = item_response.get("tokenPagination", {}).get("nextPageToken")

        return []

    def normalize(self, content):
        return {
            'type': 'youtube',
            'original_id': '',
            'original_url': '',
            'text_content': '',
            'image_url': '',
            'likes': '',
            'username': '',
            'user-image': ''
        }