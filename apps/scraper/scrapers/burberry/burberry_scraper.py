import re

from selenium.common.exceptions import NoSuchElementException
from apps.assets.models import Category

from apps.scraper.scrapers import Scraper, ProductDetailScraper, ProductCategoryScraper


class BurberryProductScraper(ProductDetailScraper):
    regexs = [r'(?:https?://)?(?:(www|ca|us)\.)?burberry\.com/([a-zA-Z0-9-_]*p\d+)/?(?:#.*)?$']

    def scrape(self, url, product, values, **kwargs):
        self.driver.get(url)

        if not product.sku:
            product.sku = self.select('.product-id.section span')[0].text

        product.price = self.select('.price-amount')[0].text
        product.name = self.select('.product-title-container h1')[0].text

        product.description = self.select('#description-panel ul')[0].get_attribute('innerHTML')
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
        images_data = [x.get_attribute('data-zoomed-src') for x in self.select('.product_viewer li.product-image')]
        if not images_data:
            return images

        for image_url in images_data:
            images.append(self._process_image(image_url, product))

        for image in product.product_images.exclude(id__in=[image.id for image in images]):
            image.delete()

        return images


class BurberryCategoryScraper(ProductCategoryScraper):
    regexs = [r'(?:https?://)?(?:(www|ca|us)\.)?burberry\.com/([^/\d]+)/?(?:#.*)?$']

    def scrape(self, url, **kwargs):
        self.driver.get(url)
        categories = self.select('.category')
        for category in categories:
            cat_name = category.find_element_by_xpath('//h2').text
            cat, _ = Category.objects.get_or_create(
                store=self.store, name=cat_name)

            products_data = category.find_elements_by_class_name('product')
            for product_data in products_data:
                product_url = product_data.find_element_by_tag_name('a').get_attribute('href')

                product = self._get_product(product_url)

                yield {'product': product, 'url': product_url,
                       'values': {
                           'category': cat_name
                       }}
