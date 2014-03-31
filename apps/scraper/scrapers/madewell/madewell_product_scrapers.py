import re

from selenium.common.exceptions import NoSuchElementException

from apps.scraper.scrapers.scraper import Scraper
from apps.assets.models import Product


class MadewellProductScraper(Scraper):
    sku_regex = r'^http://www\.madewell\.com/madewell_category/PRDOVR~(\w*)/\1\.jsp$'

    def get_regex(self, **kwargs):
        return self._wrap_regex(r'(?:www\.)?madewell\.com/madewell_category/(?:(\w*)/(?:(\w*)/)?)?PRD(?:OVR)?~(\w+)/\3\.jsp')

    def get_type(self,**kwargs):
        return self.PRODUCT_DETAIL

    def parse_url(self, url, values, **kwargs):
        match = re.match(self.get_regex(), url)
        url = 'http://www.madewell.com/madewell_category/PRDOVR~{0}/{0}.jsp'.format(match.group(3))
        category = match.group(1)
        sub_category = match.group(2)

        if category:
            values['category'] = category
            values['category_url'] = 'http://www.madewell.com/madewell_category/{0}.jsp'.format(category)
        if sub_category:
            values['sub_category'] = sub_category
            values['sub_category_url'] = 'http://www.madewell.com/madewell_category/{0}/{1}'.format(category, sub_category)

        return url

    def scrape(self, driver, url, product, values, **kwargs):
        product.sku = re.match(self.sku_regex, product.url).group(1)
        try:
            product.price = re.sub(r'USD *', '$', driver.find_element_by_class_name('selected-color-price').text)
        except NoSuchElementException:
            product.price = re.sub(r'USD *', '$', driver.find_element_by_class_name('full-price').text)

        product.name = driver.find_element_by_xpath('//section[@class="description"]/header/h1').text
        product.description = driver.find_element_by_id('prodDtlBody').get_attribute('innerHTML')

        if values.get('category', None):
            self._add_to_category(product, values.get('category', None), values.get('category_url'), None)
        if values.get('sub_category', None):
            self._add_to_category(product, values.get('sub_category', None), values.get('sub_category_url'), None)

        images = self._get_images(driver)

        product.available = True
        return product

    def _get_images(self, driver):
        images = set()
        images_data = driver.find_elements_by_xpath('//div[@class="float-left"]/img')
        if images_data:
            for img in images_data:
                image = img.get_attribute('data-imgurl')
                images.add(image)
        else:
            image = driver.find_element_by_class_name('prod-main-img').get_attribute('src')
            images.add(image)

        for image in images:
            print image

        return list(images)


class MadewellCategoryScraper(Scraper):
    def get_regex(self, **kwargs):
        return self._wrap_regex(r'(?:www\.)?madewell\.com/madewell_category/(\w*)(?:/(\w*))?\.jsp')

    def get_type(self, **kwargs):
        return self.PRODUCT_CATEGORY

    def parse_url(self, url, values, **kwargs):
        match = re.match(self.get_regex(), url)
        category = match.group(1)
        sub_category = match.group(2)
        url = 'http://www.madewell.com/madewell_category/' + category
        if sub_category:
            url += '/' + sub_category
        url += '.jsp'
        values['category'] = category
        values['category_url'] = 'http://www.madewell.com/madewell_category/{0}.jsp'.format(category)
        if sub_category:
            values['sub_category'] = sub_category
            values['sub_category_url'] = 'http://www.madewell.com/madewell_category/{0}/{1}.jsp'.format(category, sub_category)
        return url

    def scrape(self, driver, url, store, **kwargs):
        products_data = driver.find_elements_by_xpath('//td[@class="arrayProdCell"]//td[@class="arrayImg"]/a')
        for product_data in products_data:
            url = MadewellProductScraper().parse_url(product_data.get_attribute('href')).get('url')
            sku = re.match(MadewellProductScraper().sku_regex, url).group(3)
            name = product_data.find_element_by_xpath('./img').get_attribute('alt')
            try:
                product, _ = Product.objects.get(store=store, url=url)
                product.name = name
                product.sku = sku
            except Product.DoesNotExist:
                product = Product(store=store, url=url, name=name, sku=sku)

            yield product

