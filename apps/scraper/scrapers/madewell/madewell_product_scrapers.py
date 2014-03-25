import re

from selenium.common.exceptions import NoSuchElementException

from apps.scraper.scrapers.scraper import Scraper
from apps.assets.models import Product


class MadewellProductScraper(Scraper):

    sku_regex = r'^http://www.madewell.com/madewell_category/(\w*)/(\w*)/PRDOVR~(?:\w*)/(\w*).jsp$'

    def get_regex(self):
        return r'^(?:https?://)?(?:www\.)?madewell.com/madewell_category/(\w*)/(\w*)/PRD(?:OVR)?~(\w+)/\3.jsp(?:\?[^/\?]+)?$'

    def get_url(self, url):
        match = re.match(self.get_regex(), url)
        return 'http://www.madewell.com/madewell_category/{0}/{1}/PRDOVR~{2}/{2}.jsp'.format(match.group(1), match.group(2), match.group(3))

    def get_type(self):
        return self.PRODUCT_DETAIL

    def scrape(self, driver, product, **kwargs):
        product.sku = re.match(self.sku_regex, product.url).group(3)
        try:
            product.price = re.sub(r'USD *', '$', driver.find_element_by_class_name('selected-color-price').text)
        except NoSuchElementException:
            product.price = re.sub(r'USD *', '$', driver.find_element_by_class_name('full-price').text)

        product.name = driver.find_element_by_xpath('//section[@class="description"]/header/h1').text
        product.description = driver.find_element_by_id('prodDtlBody').get_attribute('innerHTML')
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
    def get_regex(self):
        return r'^(?:https?://)?(?:www\.)?madewell.com/madewell_category/(\w*)(?:/(\w*))?.jsp(?:\?[^/\?]+)?$'

    def get_url(self, url):
        match = re.match(self.get_regex(), url)
        url = 'http://www.madewell.com/madewell_category/' + match.group(1)
        if match.group(2):
            url += '/' + match.group(2)
        url += '.jsp'
        return url

    def get_type(self):
        return self.PRODUCT_CATEGORY

    def scrape(self, driver, store, **kwargs):
        urls = []
        products_data = driver.find_elements_by_xpath('//td[@class="arrayProdCell"]//td[@class="arrayImg"]/a')
        for product_data in products_data: ## need to paginate
            url = MadewellProductScraper().get_url(product_data.get_attribute('href'))
            sku = re.match(MadewellProductScraper().sku_regex, url).group(3)
            name = product_data.find_element_by_xpath('./img').get_attribute('alt')
            try:
                product, _ = Product.objects.get(store=store, url=url)
                product.name = name
                product.sku = sku
            except Product.DoesNotExist:
                product = Product(store=store, url=url, name=name, sku=sku)

            product.save()
            urls.append(url)

        return urls

