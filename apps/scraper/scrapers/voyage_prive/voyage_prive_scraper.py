# coding=utf-8
import re

from apps.assets.models import Product

from apps.scraper.scrapers.scraper import ProductCategoryScraper

from selenium.common.exceptions import NoSuchElementException


class VoyagePriveCategoryScraper(ProductCategoryScraper):
    regexs = ['https?://www.officiel-des-vacances.com/week-end']

    def get_regex(self, values, **kwargs):
        return ['https?://www.officiel-des-vacances.com/week-end']

    def parse_url(self, **kwargs):
        return 'http://www.officiel-des-vacances.com/week-end'

    def has_next_scraper(self, values, **kwargs):
        return False

    def scrape(self, url, **kwargs):
        products = []
        images = []
        self.driver.get('http://www.officiel-des-vacances.com/partners/catalog.xml')
        for node in self.driver.find_elements_by_xpath('//nodes/node'):
            sku = node.find_element_by_xpath('./id').text
            try:
                product = Product.objects.get(sku=sku)
            except Product.DoesNotExist:
                product = Product(sku=sku)
            product.store = self.store
            product.name = node.find_element_by_xpath('./titre').text
            product.url = node.find_element_by_xpath('./url-detail').text
            product.price = u'€' + node.find_element_by_xpath('./prix').text
            products.append(product)
            images.append(node.find_element_by_xpath('./image').text)
        self.driver.get(url)
        for i in range(len(products)):
            product = products[i]
            image = images[i]
            try:
                item = self.driver.find_element_by_xpath('//div[contains(div/h2/a/@href, "/{0}/")]'.format(product.sku))
                print('made it')
            except NoSuchElementException:
                continue
            product.save()
            product.default_image = self._process_image(image, product)
            product.save()
            print(product.store.id)
            yield(product)