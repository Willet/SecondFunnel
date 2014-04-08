import re

from selenium.common.exceptions import NoSuchElementException

from apps.scraper.scrapers.scraper import ProductDetailScraper, ProductCategoryScraper


class MadewellProductScraper(ProductDetailScraper):
    sku_regex = r'^http://www\.madewell\.com/madewell_category/PRDOVR~(\w+)/\1\.jsp$'

    def get_regex(self, **kwargs):
        return [self._wrap_regex(r'(?:www\.)?madewell\.com/madewell_category/(?:(\w+)/(?:(\w+)/)?)?PRD(?:OVR)?~(\w+)/\3\.jsp')]

    def parse_url(self, url, values, **kwargs):
        match = re.match(self.get_regex()[0], url)
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

    def scrape(self, url, product, values, **kwargs):
        self.driver.get(url)
        product.sku = re.match(self.sku_regex, product.url).group(1)
        try:
            product.price = re.sub(r'USD *', '$', self.driver.find_element_by_class_name('selected-color-price').text)
        except NoSuchElementException:
            product.price = re.sub(r'USD *', '$', self.driver.find_element_by_xpath('//div[@class="full-price"]/span').text)

        try:
            product.name = self.driver.find_element_by_xpath('//section[@class="description"]/header/h1').text
        except NoSuchElementException:
            product.name = self.driver.find_element_by_xpath('//section[@id="description"]/header/h1').text

        product.description = self.driver.find_element_by_id('prodDtlBody').get_attribute("innerHTML")

        product.save()

        if values.get('category', None):
            self._add_to_category(product, values.get('category', None), values.get('category_url'))
        if values.get('sub_category', None):
            self._add_to_category(product, values.get('sub_category', None), values.get('sub_category_url'))

        images = self._get_images(self.driver, product)
        product.default_image = images[0]

        product.save()

        yield product

    def _get_images(self, driver, product):
        images = []
        images_data = driver.find_elements_by_xpath('//div[@class="float-left"]/img')
        if images_data:
            for img in images_data:
                image = img.get_attribute('data-imgurl')
                images.append(self._process_image(image, product))
        else:
            image = driver.find_element_by_class_name('prod-main-img').get_attribute('src')
            images.append(self._process_image(image, product))

        for image in product.product_images.exclude(id__in=[image.id for image in images]):
            image.delete()

        return images



class MadewellCategoryScraper(ProductCategoryScraper):
    def get_regex(self, **kwargs):
        return [self._wrap_regex(r'(?:www\.)?madewell\.com/madewell_category/(\w+)(?:/(\w+))?\.jsp')]

    def parse_url(self, url, values, **kwargs):
        match = re.match(self.get_regex()[0], url)
        category = match.group(1)
        sub_category = match.group(2)
        url = 'http://www.madewell.com/madewell_category/' + category
        values['category'] = category
        values['category_url'] = 'http://www.madewell.com/madewell_category/{0}.jsp'.format(category)
        if sub_category:
            url += '/' + sub_category
            values['sub_category'] = sub_category
            values['sub_category_url'] = 'http://www.madewell.com/madewell_category/{0}/{1}.jsp'.format(category, sub_category)
        url += '.jsp'
        return url

    def scrape(self, url, store, **kwargs):
        self.driver.get(url)
        products_data = self.driver.find_elements_by_xpath('//td[@class="arrayProdCell"]//td[@class="arrayImg"]/a')
        for product_data in products_data:
            product_url = MadewellProductScraper().parse_url(product_data.get_attribute('href')).get('url')
            sku = re.match(MadewellProductScraper().sku_regex, url).group(3)
            name = product_data.find_element_by_xpath('./img').get_attribute('alt')

            product = self._get_product(product_url)

            product.name = name
            product.sku = sku

            yield product


class MadewellMultiProductScraper(ProductCategoryScraper):
    def get_regex(self, **kwargs):
        return [self._wrap_regex(r'(?:www\.)?madewell\.com/browse/multi_product_detail.jsp\?(?:[^/\?]+&)?externalProductCodes=([^&\?/]+)', True)]

    def scrape(self, url, **kwargs):
        product_codes = re.match(self.get_regex()[0], url).group(1)
        codes = product_codes.split(r'%3A')
        for sku in codes:
            if sku == '00000':
                continue
            product_url = 'http://www.madewell.com/madewell_category/PRDOVR~{0}/{0}.jsp'.format(sku)

            product = self._get_product(product_url)
            product.sku = sku

            yield product