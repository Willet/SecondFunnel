import re

from selenium.common.exceptions import NoSuchElementException

from apps.scraper.scrapers import Scraper, ProductDetailScraper, ProductCategoryScraper


class NastygalProductScraper(ProductDetailScraper):
    regexs = [r'(?:https?://)?(?:www\.)?nastygal\.com/([^/]+)/([^/]+)/?(?:#.*)?$']

    def scrape(self, url, product, values, **kwargs):
        self.driver.get(url)  # TODO: ?currency_code=USD&country_code=US

        if not product.sku:
            try:
                product.sku = re.match(r'[^\d]*(\d+)[^\d]*', self.driver.find_element_by_class_name('product-style').text).group(1)
            except NoSuchElementException:
                print "Could not find the product SKU on {0}".format(url)

        try:
            product.price = self.driver.find_element_by_class_name('current-price').text
        except NoSuchElementException:
            print "Could not find the product price on {0}".format(url)

        try:
            product.name = self.driver.find_element_by_class_name('product-name').text
        except NoSuchElementException:
            print "Could not find the product name on {0}".format(url)

        product.description = self.driver.find_element_by_class_name('product-description').get_attribute("innerHTML")
        product.save()

        if values.get('category', None):
            self._add_to_category(product, values.get('category', None), values.get('category_url'))
        if values.get('sub_category', None):
            self._add_to_category(product, values.get('sub_category', None), values.get('sub_category_url'))

        images = self._get_images(self.driver, product)
        if len(images) > 0:
            product.default_image = images[0]
            product.save()

        if self.feed:
            self.feed.add_product(product=product)

        yield {'product': product}

    def _get_images(self, driver, product):
        images = []
        try:
            images_data = [x.get_attribute('src') for x in self.driver.find_elements_by_xpath('//div[@class="carousel"]//img')]
        except NoSuchElementException:
            print "Could not product images on {0}".format(product.url)
            return images

        for image_url in images_data:
            images.append(self._process_image(image_url, product))

        for image in product.product_images.exclude(id__in=[image.id for image in images]):
            image.delete()

        return images


class NastygalCategoryScraper(ProductCategoryScraper):
    regexs = [r'(?:https?://)?(?:www\.)?nastygal\.com/([^/]+)/?(?:#.*)?$']

    def scrape(self, url, **kwargs):
        self.driver.get(url)
        products_data = self.driver.find_elements_by_xpath('//div[contains(@class, "product-list-item")]')
        for product_data in products_data:
            product_url = product_data.find_element_by_xpath('a[@class="product-link"]').get_attribute('href')
            sku = product_data.get_attribute('data-product-id')
            name = product_data.find_element_by_xpath('a/div[@class="product-name"]').text

            product = self._get_product(product_url)

            product.name = name
            product.sku = sku

            yield {'product': product, 'url': product_url}
