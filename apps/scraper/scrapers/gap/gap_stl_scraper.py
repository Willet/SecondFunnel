import re

from selenium.common.exceptions import NoSuchElementException

from apps.scraper.scrapers import Scraper, ContentDetailScraper
from apps.assets.models import Image, Product


class STLScraper(ContentDetailScraper):
    regexs = [Scraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?([^/\?]*&)*cid=(\d*)(&[^/\?]*)*&oid=(OUT-\d+)', True),
              Scraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?([^/\?]*&)*oid=(OUT-\d+)(&[^/\?]*)*&cid=(\d*)', True)]

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={0}&oid={1}'.format(match.group(1), match.group(2))
        match = re.match(self.regexs[1], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={1}&oid={0}'.format(match.group(1), match.group(2))

    def scrape(self, url, **kwargs):
        self.driver.get(url)
        outfit_content = self.driver.find_element_by_xpath('//div[@id="outfitContent"')
        image_url = outfit_content.find_element_by_xpath('./div[@id="outfitContentLeft"]/div[@id="outfitImage"]//img').get_attribute('src')
        if image_url.startswith('/'):
            image_url = 'http://www.gap.com' + image_url
        try:
            image = Image.objects.get(store=self.store, original_url=url)
        except Image.DoesNotExist:
            image = Image(store=self.store, source_url=image_url)
        image = self._process_image(image_url, image)
        image.original_url = url
        image.source = 'gap-stl'
        image.save()
        for product_elem in outfit_content.find_elements_by_xpath('./div[@id="outfitContentRight"]//div[contains(@id, "product")]'):
            product_name = product_elem.fin_element_by_xpath('.//p[class="productName"]/span').text
            try:
                product = Product.objects.get(store=self.store, name=product_name)
                image.tagged_products.add(product)
            except Product.DoesNotExist:
                pass
        yield {'content': image}
