import re

from selenium.common.exceptions import NoSuchElementException

from apps.scraper.scrapers.scraper import ContentDetailScraper, ContentCategoryScraper
from apps.assets.models import Image


class StyldByPartnersScraper(ContentCategoryScraper):
    SOURCE = 'styld-by'

    def get_regex(self, **kwargs):
        return [self._wrap_regex('(?:www\.)?styld-by\.com/en-us/partners/([\w\-]*)/([\w\-]*)/?')]

    def parse_url(self, url, **kwargs):
        match = re.match(self.get_regex()[0], url)
        return 'http://www.styld-by.com/en-us/partners/{0}/{1}'.format(match.group(1), match.group(2))

    def has_next_scraper(self, **kwargs):
        return False

    def scrape(self, driver, url, **kwargs):
        self.driver.get(url)
        name = driver.find_element_by_xpath('.//h2[@class="title"]').text
        description = driver.find_element_by_xpath('.//div[@class="content"]/p').text
        author = driver.find_element_by_xpath('.//div[@class="contributor"]/a').text
        for image_element in driver.find_elements_by_xpath('.//div[@class="swipe"]//div[@class="bandwrapper"]/img'):
            image_url = image_element.get_attribute('data-src').replace('medium', 'large')
            image_url = image_url.split('?')[0]
            try:
                image = Image.objects.get(store=self.store, original_url=url, source_url=image_url)
            except Image.DoesNotExist:
                image = Image(store=self.store, original_url=url, source_url=image_url)
            image.name = name
            image.description = description
            image.author = author
            image.source = self.SOURCE
            image = self._process_image(image_url, image)
            image.save()
            yield image


class StyldByFilterScraper(ContentCategoryScraper):
    SOURCE = 'styld-by'

    def get_regex(self, **kwargs):
        return [self._wrap_regex('(?:www\.)?styld-by\.com/en-us/filter/([\w\-]*)/?')]

    def parse_url(self, url, **kwargs):
        match = re.match(self.get_regex()[0], url)
        return 'http://www.styld-by.com/en-us/filter/{0}'.format(match.group(1))

    def has_next_scraper(self, **kwargs):
        return False

    def scrape(self, driver, url, values, **kwargs):
        page = 1
        while True:
            self.driver.get(url + '/page/' + str(page))
            for element in driver.find_elements_by_xpath('//div[@role="main"]/ul/li/article'):
                title_element = element.find_element_by_xpath('.//h2[@class="title"]/a')
                name = title_element.text
                original_url = title_element.get_attribute('href')
                description = element.find_element_by_xpath('.//div[@class="content"]/p').text
                author = element.find_element_by_xpath('.//div[@class="contributor"]/a').text
                for image_element in element.find_elements_by_xpath('.//div[@class="swipe"]//div[@class="bandwrapper"]/img'):
                    image_url = image_element.get_attribute('data-src').replace('medium', 'large')
                    try:
                        image = Image.objects.get(store=self.store, original_url=original_url, source_url=image_url)
                    except Image.DoesNotExist:
                        image = Image(store=self.store, original_url=original_url, source_url=image_url)
                    image.name = name
                    image.description = description
                    image.author = author
                    image.source = self.SOURCE
                    image = self._process_image(image_url, image)
                    image.save()
                    yield image
            try:
                driver.find_element_by_xpath('//div[@class="pagination"]/a[@rel="next"]')
                page += 1
            except NoSuchElementException:
                break
