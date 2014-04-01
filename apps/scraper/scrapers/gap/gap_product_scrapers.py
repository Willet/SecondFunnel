import re

from selenium.common.exceptions import NoSuchElementException

from apps.scraper.scrapers.scraper import ProductDetailScraper, ProductCategoryScraper
from apps.assets.models import Product


class GapProductScraper(ProductDetailScraper):
    sku_regex = r'^http://www\.gap\.com/browse/product\.do\?pid=(\d{6})$'
    imageLabels = ["Z", "AV1_Z", "AV2_Z", "AV9_Z", "SC_OUT_Z"]

    def get_regex(self, **kwargs):
        return [self._wrap_regex(r'(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*', True)]

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/product.do?pid=' + re.match(self.get_regex()[0], url).group(1)

    def scrape(self, driver, url, product, **kwargs):
        try:
            product.name = driver.find_element_by_class_name('productName').text
        except NoSuchElementException:
            yield product
            return
        product.sku = re.match(self.sku_regex, product.url).group(1)
        product.description = driver.find_element_by_id('tabWindow').get_attribute('innerHTML')
        product.price = driver.find_element_by_id('priceText').text
        driver.get('http://www.gap.com/browse/productData.do?pid=%s' % product.sku)

        product.save()

        self._get_images(driver.page_source, product)

        yield product

    def _get_images(self, product_data_page, product):
        picture_groups = re.finditer(re.compile(r"styleColorImagesMap\s*=\s*\{\s*([^\}]*)\}\s*;", flags=re.MULTILINE|re.DOTALL), product_data_page)
        for group_match in picture_groups:
            images_text = group_match.group(1)
            pictures = re.finditer(re.compile(r"\s*'([^\']+)'\s*:\s*'([^\']+)'", flags=re.MULTILINE|re.DOTALL), images_text)
            for pictures_match in pictures:
                name = pictures_match.group(1)
                url = pictures_match.group(2)
                if name in self.imageLabels:
                    if url.startswith('/'):
                        url = 'http://www.gap.com' + url
                    self._process_image(url, product)


class GapCategoryScraper(ProductCategoryScraper):
    product_sku_regex = r'^(?:(?:https?://)?(?:www\.)?gap\.com)?/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&[^/\?]*)?$'

    def get_regex(self, **kwargs):
        return [self._wrap_regex(r'(?:www\.)?gap\.com/browse/category\.do\?[^/\?]*cid=(\d*)', True)]

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/category.do?cid=' + re.match(self.get_regex()[0], url).group(1)

    def scrape(self, driver, url, **kwargs):
        page_text = driver.find_element_by_xpath('//label[@class="pagePaginatorLabel"]').text
        if page_text:
            pages = int(re.match(r'Page *\d+ *of *(\d+)', page_text).group(1))
        else:
            pages = 1
        page = 0
        while page < int(pages):
            driver.get(url + '#pageId=' + str(page))
            for product_elem in driver.find_elements_by_xpath('//div[@id="mainContent"]//ul/li/div/a'):
                href = product_elem.get_attribute('href')
                match = re.match(self.product_sku_regex, href)
                if not match:
                    continue
                sku = match.group(1)
                url = 'http://www.gap.com/browse/product.do?pid=' + sku
                name = product_elem.find_element_by_xpath('.//img').get_attribute('alt')

                try:
                    product = Product.objects.get(store=self.store, url=url)
                    product.sku = sku
                    product.name = name
                except Product.DoesNotExist:
                    product = Product(store=self.store, url=url, sku=sku, name=name)
                    last = Product.objects.all().order_by('-old_id')[0]
                    product.old_id = last.old_id + 1
                yield product
            page += 1
