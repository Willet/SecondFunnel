# coding=utf-8
import re

from apps.assets.models import Product

from apps.scraper.scrapers import ProductCategoryScraper

from selenium.common.exceptions import NoSuchElementException


class VoyagePriveCategoryScraper(ProductCategoryScraper):
    regexs = ['https?://www.officiel-des-vacances.com/week-end']

    def parse_url(self, **kwargs):
        return 'http://www.officiel-des-vacances.com/week-end'

    def scrape(self, url, **kwargs):
        products = []
        images = []
        print('loading url http://www.officiel-des-vacances.com/partners/catalog.xml')
        self.driver.get('http://www.officiel-des-vacances.com/partners/catalog.xml')
        print('url loaded')
        for node in self.driver.find_elements_by_xpath('//nodes/node'):
            sku = node.find_element_by_xpath('./id').text
            try:
                product = Product.objects.get(sku=sku)
            except Product.DoesNotExist:
                product = Product(sku=sku)
            product.store = self.store
            product.name = node.find_element_by_xpath('./titre').text
            match = re.match(r"""(.+),?         # Name of product
                                 \s?            # Followed by 0 or 1 space
                                 (-\s?\d+%)     # Percentage of product off
                              """, product.name, re.VERBOSE)
            if match:
                product.name = match.group(1)
                product.attributes['discount'] = match.group(2)
            product.url = node.find_element_by_xpath('./url').text
            product.price = u'€' + node.find_element_by_xpath('./prix').text
            products.append(product)
            images.append(node.find_element_by_xpath('./image').text)
        print('loading url ' + url)
        self.driver.get(url)
        print('url loaded')
        for i in range(len(products)):
            product = products[i]
            image = images[i]
            try:
                item = self.driver.find_element_by_xpath('//div[contains(div/h2/a/@href, "/{0}/")]'.format(product.sku))
            except NoSuchElementException:
                continue
            product.save()
            product.default_image = self._process_image(image, product)
            product.save()
            yield {'product': product}