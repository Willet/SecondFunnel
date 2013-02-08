class Social(object):
    def __init__(self, *args, **kwargs):
        tokens = kwargs.get('tokens')

        if tokens:
            self.access_token = tokens.get('access_token')

        if not self.access_token:
            raise

    def _fetch_media(self):
        return []

    def get_content(self, since=None, limit=-1):
        """Returns a list of content in a standard format."""
        results = self._fetch_media(since=since)

        content = []
        for result in results:
            if limit > 0:
                break
            content.append(self.normalize(result))
            limit -= 1

        return content

    def normalize(self, content):
        """Converts content from a service into a regular format"""
        return content

        # What common operations will there be?
        #   Access 'content'
        #       What is content? Images? Posts? Etc.
        #       ...Is that it? Really?
        #           Well, we'll need to marshall the content, maybe fetch it offline...