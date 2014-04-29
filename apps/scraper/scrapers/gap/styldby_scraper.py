import re

from apps.scraper.scrapers.scraper import Scraper, ContentCategoryScraper
from apps.assets.models import Image


class StyldByPartnersScraper(ContentCategoryScraper):
    regexs = [Scraper._wrap_regex('(?:www\.)?styld-by\.com/en-us/partners/([\w\-]*)/([\w\-]*)/?')]
    SOURCE = 'styld-by'

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        return 'http://www.styld-by.com/en-us/partners/{0}/{1}'.format(match.group(1), match.group(2))

    def process(self, url, page, text='', status=200, **kwargs):
        name = page.select('h2.title')[0].text
        description = page.select('div.content p')[0].text
        author = page.select('div.contributor a')[0].text
        for image_element in page.select('div.swipe div.bandwrapper img'):
            image_url = image_element.attrs.get('data-src').replace('medium', 'large')
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

            print "Saving styld.by content {0}".format(image)
            image.save()


class StyldByFilterScraper(ContentCategoryScraper):
    regexs = [Scraper._wrap_regex('(?:www\.)?styld-by\.com/en-us/filter/([\w\-]*)/?')]
    SOURCE = 'styld-by'

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        return 'http://www.styld-by.com/en-us/filter/{0}'.format(match.group(1))

    def process(self, url, page, text='', status=200, **kwargs):
        page_num = 1
        while True:
            _, status, page, _ = self.scrape(urls='%s/page/%s' % (url, page_num))[0]
            for element in page.select("div[role='main'] ul li article"):
                title_element = element.select('h2.title a')[0]
                name = title_element.text
                original_url = title_element.attrs.get('href')
                description = element.select('div.content p')[0].text
                author = element.select('div.contributor a')[0].text
                for image_element in element.select('div.swipe div.bandwrapper img'):
                    image_url = image_element.attrs.get('data-src').replace('medium', 'large')
                    try:
                        image = Image.objects.get(store=self.store, original_url=original_url, source_url=image_url)
                    except Image.DoesNotExist:
                        image = Image(store=self.store, original_url=original_url, source_url=image_url)
                    image.name = name
                    image.description = description
                    image.author = author
                    image.source = self.SOURCE
                    image = self._process_image(image_url, image)

                    print "Saving styld.by content {0}".format(image)
                    image.save()
            try:
                page.select("div.pagination a[rel='next']")
                page_num += 1
            except IndexError:
                break
