from apps.assets.models import Product
import re

def scrape_product_page(product, driver):
    sku_regex = r'^http://www\.gap\.com/browse/product\.do\?pid=(\d{6})$'

    product.sku = re.match(sku_regex, product.url).group(1)
    product.name = driver.find_element_by_class_name('productName').text
    product.description = driver.find_element_by_id('tabWindow').get_attribute('innerHTML')
    product.price = driver.find_element_by_id('priceText').text
    return product

def scrape_category_page(store, driver):
    sku_regex = r'^(?:https?://)?(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&.*)?$'

    for product_elem in driver.find_elements_by_xpath('//div[@id="mainContent"]//ul/li/div/a'):
        href = product_elem.get_attribute('href')

        sku = re.match(sku_regex, href).group(1)
        url = 'http://www.gap.com/browse/product.do?pid=' + sku
        name = product_elem.find_element_by_xpath('.//img').get_attribute('alt')

        try:
            product, _ = Product.objects.get(store=store, url=url)
            product.sku = sku
            product.name = name
            yield product
        except Product.DoesNotExist:
            yield Product(store=store, url=url, sku=sku, name=name)
