import re

from apps.scraper.scrapers.scraper import ContentDetailScraper, ContentCategoryScraper
from apps.assets.models import Image


class PinterestPinScraper(ContentDetailScraper):
    SOURCE = 'pinterest'

    def get_regex(self, **kwargs):
        return [self._wrap_regex(r'(?:www\.)?pinterest\.com/pin/(\d*)/?')]

    def parse_url(self, url, **kwargs):
        sku = re.match(self.get_regex()[0], url).group(1)
        return 'http://www.pinterest.com/pin/{0}/'.format(sku)

    def scrape(self, driver, url, content, **kwargs):
        driver.get(url)
        if content is None:
            try:
                content = Image.objects.get(store=self.store, original_url=url)
            except Image.DoesNotExist:
                content = Image(store=self.store, original_url=url)
        content.description = driver.find_element_by_class_name('commentDescriptionContent').text
        content.source = self.SOURCE
        content = self._process_image(driver.find_element_by_xpath('//div[@class="imageContainer"]/img').get_attribute('src'), content)
        yield content


class PinterestAlbumScraper(ContentCategoryScraper):

    def get_regex(self, **kwargs):
        return [self._wrap_regex(r'(?:www\.)?pinterest\.com/(\w*)/(\w*)/?')]

    def parse_url(self, url, **kwargs):
        match = re.match(self.get_regex()[0], url)
        user = match.group(1)
        album = match.group(2)
        return 'http://www.pinterest.com/{0}/{1}/'.format(user, album)

    def scrape(self, driver, url, **kwargs):
        driver.get(url)
        for element in driver.find_elements_by_xpath('//div[@class="pinHolder"]/a'):
            url = element.get_attribute('href')
            try:
                content = Image.objects.get(store=self.store, original_url=url)
            except Image.DoesNotExist:
                content = Image(store=self.store, original_url=url)
            content.source = 'pinterest'

            yield content, url
