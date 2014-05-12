import re
from time import sleep

from apps.scraper.scrapers import Scraper, ContentDetailScraper, ContentCategoryScraper
from apps.assets.models import Image


class PinterestPinScraper(ContentDetailScraper):
    """pinterest.com/pin/(some very large number)"""
    regexs = [Scraper._wrap_regex(r'(?:www\.)?pinterest\.com/pin/(\d*)/?')]
    SOURCE = 'pinterest'

    def parse_url(self, url, **kwargs):
        sku = re.match(self.regexs[0], url).group(1)
        return 'http://www.pinterest.com/pin/{0}/'.format(sku)

    def scrape(self, url, content, **kwargs):
        print "Loading pinterest item {}".format(url)
        self.driver.get(url)
        if content is None:
            try:
                content = Image.objects.get(store=self.store, original_url=url)
            except Image.DoesNotExist:
                content = Image(store=self.store, original_url=url)
        content.description = self.driver.find_element_by_class_name('commentDescriptionContent').text
        content.source = self.SOURCE
        source_url = self.driver.find_element_by_xpath('//div[@class="imageContainer"]/img').get_attribute('src')
        content = self._process_image(source_url, content)
        content.save()
        yield {'content': content}


class PinterestAlbumScraper(ContentCategoryScraper):
    """pinterest.com/user_name/album_name"""
    regexs = [Scraper._wrap_regex(r'(?:www\.)?pinterest\.com/(\w+)/(\w+)/?')]

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        user = match.group(1)
        album = match.group(2)
        return 'http://www.pinterest.com/{0}/{1}/'.format(user, album)

    def scrape(self, url, **kwargs):
        self.driver.get(url)
        pins, pin_count = [], 0
        while True:
            # scroll until we don't have more pins
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)

            pins = self.driver.find_elements_by_xpath(
                '//div[contains(@class, "GridItems")]/div[contains(@class, "item")]')
            if len(pins) <= pin_count:
                break

            pin_count = len(pins)
            print "Retrieving {} pins...".format(pin_count)

        for element in pins:
            url = element.find_element_by_css_selector('.pinHolder a').get_attribute('href')
            try:
                content = Image.objects.get(store=self.store, original_url=url)
            except Image.DoesNotExist:
                content = Image(store=self.store, original_url=url)
            content.source = 'pinterest'

            yield {'content': content, 'url': url}
