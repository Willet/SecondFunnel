import re

from apps.scraper.scrapers.scraper import Scraper
from apps.assets.models import Product


class GapProductScraper(Scraper):
    sku_regex = r'^http://www\.gap\.com/browse/product\.do\?pid=(\d{6})$'
    imageLabels = ["Z", "AV1_Z", "AV2_Z", "AV9_Z", "SC_OUT_Z"]

    def get_regex(self):
        return r'^(?:https?://)?(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&[^/\?]*)?$'

    def get_url(self, url):
        return 'http://www.gap.com/browse/product.do?pid=' + re.match(self.get_regex(), url).group(1)

    def get_type(self):
        return self.PRODUCT_DETAIL

    def scrape(self, driver, product, **kwargs):
        product.sku = re.match(self.sku_regex, product.url).group(1)
        product.name = driver.find_element_by_class_name('productName').text
        product.description = driver.find_element_by_id('tabWindow').get_attribute('innerHTML')
        product.price = driver.find_element_by_id('priceText').text
        driver.get('http://www.gap.com/browse/productData.do?pid=%s' % product.sku)

        self._get_images(driver.page_source)

        return product

    def _get_images(self, product_data_page):
        images = set()
        picture_groups = re.finditer(re.compile(r"styleColorImagesMap\s*=\s*\{\s*([^\}]*)\}\s*;", flags=re.MULTILINE|re.DOTALL), product_data_page)
        for group_match in picture_groups:
            images_text = group_match.group(1)
            pictures = re.finditer(re.compile(r"\s*'([^\']+)'\s*:\s*'([^\']+)'", flags=re.MULTILINE|re.DOTALL), images_text)
            for pictures_match in pictures:
                name = pictures_match.group(1)
                url = pictures_match.group(2)
                if name in self.imageLabels:
                    images.add(url)

        return list(images)


class GapCategoryScraper(Scraper):
    product_sku_regex = r'^(?:https?://)?(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&[^/\?]*)?$'

    def get_regex(self):
        return r'^(?:https?://)?(?:www\.)?gap\.com/browse/category\.do\?[^/\?]*cid=(\d{6})\d*(?:&[^/\?]*)?$'

    def get_url(self, url):
        return 'http://www.gap.com/browse/category.do?cid=' + re.match(self.get_regex(), url).group(1)

    def get_type(self):
        return self.PRODUCT_CATEGORY

    def scrape(self, driver, store, **kwargs):
        products = []
        for product_elem in driver.find_elements_by_xpath('//div[@id="mainContent"]//ul/li/div/a'):
            href = product_elem.get_attribute('href')

            sku = re.match(self.product_sku_regex, href).group(1)
            url = 'http://www.gap.com/browse/product.do?pid=' + sku
            name = product_elem.find_element_by_xpath('.//img').get_attribute('alt')

            try:
                product, _ = Product.objects.get(store=store, url=url)
                product.sku = sku
                product.name = name
                products.append(product)
            except Product.DoesNotExist:
                products.append(Product(store=store, url=url, sku=sku, name=name))

        return products
