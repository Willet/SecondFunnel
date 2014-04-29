import re

from apps.scraper.scrapers.scraper import Scraper, ContentDetailScraper, ContentCategoryScraper
from apps.assets.models import Image


class PinterestPinScraper(ContentDetailScraper):
    """Constructor requires a 'store' kwarg."""
    regexs = [Scraper._wrap_regex(r'(?:www\.)?pinterest\.com/pin/(\d*)/?')]
    SOURCE = 'pinterest'

    def parse_url(self, url, **kwargs):
        sku = re.match(self.regexs[0], url).group(1)
        return 'http://www.pinterest.com/pin/{0}/'.format(sku)

    def process(self, url, page, text='', status=200, **kwargs):
        content = kwargs.get('content')
        if content is None:
            try:
                content = Image.objects.get(store=self.store, original_url=url)
            except Image.DoesNotExist:
                content = Image(store=self.store, original_url=url)

        content.description = page.select('.commentDescriptionContent')[0].text
        content.source = self.SOURCE
        source_url = page.select('div.imageContainer img').attrs.get('src')
        content = self._process_image(source_url, content)

        print "Saving pinterest content {0}".format(content)
        content.save()
        # return {'content': content}


class PinterestAlbumScraper(ContentCategoryScraper):
    """Constructor requires a 'store' kwarg."""
    regexs = [Scraper._wrap_regex(r'(?:www\.)?pinterest\.com/(\w*)/(\w*)/?')]

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        user = match.group(1)
        album = match.group(2)
        return 'http://www.pinterest.com/{0}/{1}/'.format(user, album)

    def process(self, url, page, text='', status=200, **kwargs):
        for element in page.select('div.pinHolder a'):
            url = element.get_attribute('href')
            try:
                content = Image.objects.get(store=self.store, original_url=url)
            except Image.DoesNotExist:
                content = Image(store=self.store, original_url=url)

            content.source = 'pinterest'

            print "Saving pinterest content {0}".format(content)
            content.save()
            # return {'content': content, 'url': url}
