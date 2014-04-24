import re

from apps.scraper.scrapers import Scraper, ContentDetailScraper
from apps.assets.models import Image, Product


class STLScraper(ContentDetailScraper):
    regexs = [Scraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?(?:[^/\?]*&)*cid=(\d+)(?:&[^/\?]*)*&oid=(OUT-\d+)', True),
              Scraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?(?:[^/\?]*&)*oid=(OUT-\d+)(?:&[^/\?]*)*&cid=(\d+)', True)]

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={0}&oid={1}'.format(match.group(1), match.group(2))
        match = re.match(self.regexs[1], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={1}&oid={0}'.format(match.group(1), match.group(2))

    def scrape(self, url, **kwargs):
        print('loading url ' + url)
        self.driver.get(url)
        print('url loaded')
        outfit_content = self.driver.find_element_by_xpath('//div[@id="outfitContent"]')
        image_url = outfit_content.find_element_by_xpath('./div[@id="outfitContentLeft"]/div[@id="outfitImages"]//img').get_attribute('src')
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
        for product_match in re.finditer('objGIDPageViewAdapter\.objGIDOutfit\.arrayProducts\.push\(\{strProductId:\s"(\d+)',
                                         self.driver.page_source):
            sku = product_match.group(1)
            try:
                product = Product.objects.get(store=self.store, sku=sku)
                image.tagged_products.add(product)
            except Product.DoesNotExist:
                yield {'url': 'http://www.gap.com/browse/product.do?pid=' + sku}
                product = Product.objects.get(store=self.store, sku=sku)
                image.tagged_products.add(product)
                pass
        yield {'content': image}
