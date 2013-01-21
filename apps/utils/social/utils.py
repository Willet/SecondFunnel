class Social(object):
    def __init__(self, *args, **kwargs):
        tokens = kwargs.get('tokens')

        if tokens:
            self.access_token = tokens.get('access_token')

        if not self.access_token:
            raise

    def _fetch_media(self):
        return []

    def get_content(self):
        """Returns a list of content in a standard format."""
        results = self._fetch_media()

        content = []
        for result in results:
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