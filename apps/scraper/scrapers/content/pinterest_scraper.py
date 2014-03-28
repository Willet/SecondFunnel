import re

from apps.scraper.scrapers.scraper import Scraper
from apps.assets.models import Image

class PinterestPinScraper(Scraper):

    def get_regex(self, **kwargs):
        return r'^(?:https?://)(?:www\.)pinterest\.com/pin/(\d*)/?$'

    def get_type(self, **kwargs):
        self.CONTENT_DETAIL

    def parse_url(self, url, **kwargs):
        sku = re.match(self.get_regex(), url)
        return 'http://www.pinterest.com/pin/{0}/'.format(sku)

    def scrape(self, driver, url, content, **kwargs):
        if content is None:
            try:
                content = Image.objects.get(store=self.store, source_url=url)
            except Image.DoesNotExist:
                content = Image(store=self.store, source_url=url)
        content.source_url = url
        content.original_url = driver.find_element_by_xpath('//div[@class=imageContainer]/img').get_attribute('src')
        content.url = self._process_image()
        content.description = driver.find_element_by_class_name('commentDescriptionContent').text