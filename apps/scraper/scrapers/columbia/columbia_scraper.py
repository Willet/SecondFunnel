import re
import urlparse
from selenium.common.exceptions import NoSuchElementException

from apps.assets.models import Category
from apps.scraper.scrapers import ProductDetailScraper, ProductCategoryScraper


class ColumbiaProductScraper(ProductDetailScraper):
    regexs = [r'(?:https?://)?(?:www\.)?columbia\.com/(.+pd\.html.*)$']

    def scrape(self, url, values, **kwargs):
        self.driver.get(url)
        print('loaded url ' + url)

        category_name = values.get('category', None)
        product = kwargs.get('product', None)
        if not product:
            product = self._get_product(url)

        try:
            product.sku = self.find('//span[@itemprop="identifier"]').text.lstrip('#')
        except NoSuchElementException:
            print "Product sku not found!"

        try:
            product.name = self.find('.product_title').text
        except NoSuchElementException:
            print "Product name not found!"

        try:
            product.price = self.find('.price-index.regprice').text
        except NoSuchElementException:
            print "Product price not found!"

        try:
            product.description = self.find('.description').text.replace(u'\xbb', '')  # is unicode
        except NoSuchElementException:
            print "Product description not found!"

        try:
            product.details = self.find('.pdpDetailsContent').get_attribute('innerHTML').replace('\t', '')
        except NoSuchElementException:
            print "Product details not found!"

        product.save()

        # if you're lucky, you get 'ColumbiaSportswear/S13_FM7266_486_s' here
        product_image_id = re.findall(
            r'image=([^&]+)&',
            self.find('//div[@id="flashcontent"]/*').get_attribute('outerHTML'),
            re.I | re.U | re.M)[0]
        master_image_url = "http://s7d5.scene7.com/is/image/{0}?scl=1&fmt=jpeg".format(
            product_image_id)

        # because there isn't a way to find more images in the flash object,
        # this product has one product image
        product.default_image = self._process_image(master_image_url, product)
        product.product_images = [product.default_image]
        product.save()

        yield {'product': product}


class ColumbiaCategoryScraper(ProductCategoryScraper):
    """Actually scrapes Columbia's subcategories (where products are listed)."""
    regexs = [r'(?:https?://)?(?:www\.)?columbia\.com/(.+sc\.html.*)$']

    def scrape(self, url, values, **kwargs):
        page_number = 1
        self.driver.get(url)
        print('loaded url ' + url)

        num_pages = 1
        for x in self.select('.pagination .pages a'):
            if x.text.isdigit() and int(x.text) > num_pages:
                num_pages = int(x.text)

        # http://www.columbia.com/mens/men,default,sc.html?prefn1=collection&amp;prefv1=PFG&amp;start=24&amp;sz=24
        while page_number <= num_pages:  # TODO: Check for ">>"
            category_name = self.select('#breadcrumb a')[1].text
            product_elems = self.select(".result-item")
            for product_elem in product_elems:
                product_link_el = product_elem.find_element_by_css_selector('.prod-model a')
                product_url = product_link_el.get_attribute('href')
                product = self._get_product(product_url)

                product.name = product_link_el.text
                product.price = product_elem.find_element_by_css_selector('.price-index.regprice').text
                print u"Scraping product '{}'...".format(product.name)
                yield {'product': product, 'url': product_url, 'values': {
                    'category': category_name}}

            # next page, unless... no more pages
            page_number += 1
            comps = urlparse.urlparse(url)

            # paginate (up by 24)
            url = urlparse.urlunparse((comps.scheme, comps.netloc, comps.path,
                '',
                'prefn1=collection&amp;prefv1={0}&amp;start={1}&amp;sz=24'.format(
                    category_name.upper(), page_number * 24),
                ''))
            self.driver.get(url)
            print('loaded url ' + url)
