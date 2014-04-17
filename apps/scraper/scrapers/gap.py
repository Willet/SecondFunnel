import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from apps.scraper.models import Spider, ProductDetailSpider, ProductCategorySpider


class GapProductSpider(ProductDetailSpider):
    regexs = [Spider._wrap_regex(r'(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*', True)]
    sku_regex = r'^http://www\.gap\.com/browse/product\.do\?pid=(\d{6})$'
    imageLabels = ["Z", "AV1_Z", "AV2_Z", "AV9_Z", "SC_OUT_Z"]

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/product.do?pid=' + re.match(self.regexs[0], url).group(1)

    def parse(self, url, values, **kwargs):
        product = kwargs.get('product')
        url = self._wrap_url(url)
        print('loading ' + url)
        # self.driver.get(url)
        page_source, page = self.scrape(url=url)
        print('loaded')
        try:
            product.name = page.select('span.productName')[0].text
        except IndexError:  # only pages with ^ is in stock
            product.in_stock = False
            product.save()
            yield {'product': product}
            return

        # retrieve the price of the product
        try:
            product.price = page.select('span#priceText')[0].text
        except IndexError:  # original price not found; guess
            try:
                product.price = page.select('#priceText')[0].text
            except:
                pass

        # retrieve the sale price of the product
        try:
            sale_price = page.select('span.salePrice')[0].text
            product.attributes.update({'sale_price': sale_price})
        except IndexError:
            try:
                sale_price_text = page.select('#productPageMupMessageStyle')[0].text
                match = re.match(r'Now (\$\d+\.\d{2})', sale_price_text)
                if match:
                    sale_price = match.group(1)
                    product.attributes.update({'sale_price': sale_price})
                else:
                    product.attributes.pop('sales_price', None)
            except IndexError:
                product.attributes.pop('sales_price', None)

        product.sku = re.match(self.sku_regex, product.url).group(1)
        product.description = str(page.select('#tabWindow')[0])

        product.save()

        # retrieving the major category for the product
        try:
            category_elem = page.select('li a._selected')[0]
            category_url = category_elem.get_attribute('href')
            if category_url.startswith('/'):
                category_url = 'http://www.gap.com' + category_url
            # using innerHTML because category_elem.text does not seem to work here
            category_name = category_elem.get_attribute('innerHTML').replace('<p>', '').replace('</p>', '')
            if category_name == 'body' or category_name == 'gapfit' or category_name == 'maternity':
                self._add_to_category(product, 'women', 'http://www.gap.com/browse/subDivision.do?cid=5646')
            else:
                self._add_to_category(product, category_name, category_url)
        except IndexError:
            pass

        if values.get('category', None):
            self._add_to_category(product, values.get('category', None))
        if values.get('sub_category', None):
            self._add_to_category(product, values.get('sub_category', None))

        # given a url, scrape some other url (the same product's data json)
        page_source, page = self.scrape('http://www.gap.com/browse/productData.do?pid=%s' % product.sku)

        images = self._get_images(page_source, product)
        if len(images) > 0:
            product.default_image = images[0]
            product.save()

        yield {'product': product}

    def start_requests(self):
        pass

    def _get_images(self, product_data_page, product):
        """
        Retrieves the images for the specified product from the gap website
        Removes all old product images from the product by deleting them
        """
        images = []
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
                    images.append(self._process_image(url, product))

        if len(images) == 0:
            return images

        for image in product.product_images.exclude(id__in=[image.id for image in images]):
            image.delete()

        return images


class GapCategorySpider(ProductCategorySpider):
    regexs = [Spider._wrap_regex(r'(?:www\.)?gap\.com/browse/category\.do\?[^/\?]*cid=(\d*)', True)]
    product_sku_regex = r'^(?:(?:https?://)?(?:www\.)?gap\.com)?/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&[^/\?]*)?$'

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/category.do?cid=' + re.match(self.regexs[0], url).group(1)

    def parse(self, url, values, **kwargs):
        self.driver.get(url)

        # get category name
        try:
            values['category'] = self.driver.find_element_by_xpath('//span[@id="subcatname"]').text.strip()
        except NoSuchElementException:
            pass

        # get number of pages
        try:
            page_text = self.driver.find_element_by_xpath('//label[@class="pagePaginatorLabel"]').text
            if page_text:
                pages = int(re.match(r'Page *\d+ *of *(\d+)', page_text).group(1))
            else:
                pages = 1
        except NoSuchElementException:
            pages = 1
        page = 0
        while page < pages:
            self.driver.get(url + '#pageId=' + str(page))

            # get all sub categories on the page
            try:
                sub_categories = self.driver.find_elements_by_xpath('//div[@id="mainContent"]//div[@class="clearfix"]/h2')
            except NoSuchElementException:
                sub_categories = []

            product_groups = self.driver.find_elements_by_xpath('//div[@id="mainContent"]//div[@class="clearfix"]/ul')

            for i in range(len(product_groups)):
                if sub_categories:
                    values['sub_category'] = sub_categories[i].text
                else:
                    values['sub_category'] = None
                for product_elem in product_groups[i].find_elements_by_xpath('./li/div/a'):
                    href = product_elem.get_attribute('href')
                    match = re.match(self.product_sku_regex, href)
                    if not match:
                        continue
                    sku = match.group(1)
                    product_url = 'http://www.gap.com/browse/product.do?pid=' + sku
                    name = product_elem.find_element_by_xpath('.//img').get_attribute('alt')

                    product = self._get_product(product_url)
                    product.sku = sku
                    product.name = name
                    yield {'product': product, 'url': product_url}
            page += 1
