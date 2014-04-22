# coding=utf-8
import re

from apps.assets.models import Product

from apps.scraper.scrapers import ProductCategoryScraper
from selenium.common.exceptions import NoSuchElementException


class VoyagePriveCategoryScraper(ProductCategoryScraper):
    regexs = ['https?://www.officiel-des-vacances.com/week-end']

    def parse_url(self, **kwargs):
        return 'http://www.officiel-des-vacances.com/week-end'

    def scrape(self, url, **kwargs):
        products = []
        images = []
        print('loading url http://www.officiel-des-vacances.com/partners/catalog.xml')
        self.driver.get('http://www.officiel-des-vacances.com/partners/catalog.xml')
        print('url loaded')
        for node in self.driver.find_elements_by_xpath('//nodes/node'):
            sku = node.find_element_by_xpath('./id').text
            direct_site_name = node.find_element_by_xpath('./nom-fournisseur').text
            direct_site_image = node.find_element_by_xpath('./image-fournisseur').text
            try:
                product = Product.objects.filter(sku=sku)[0]
            except (Product.DoesNotExist, IndexError):
                product = Product(sku=sku)
            product.store = self.store
            product.name = node.find_element_by_xpath('./titre').text
            match = re.match(r"""(.+),?         # Name of product
                                 \s?            # Followed by 0 or 1 space
                                 (-\s?\d+%)     # Percentage of product off
                              """, product.name, re.VERBOSE)
            if match:
                product.name = match.group(1).strip()
                product.attributes['discount'] = match.group(2)

            # in no position of the product name is 'jusqu'à' a useful term to keep
            product.name = product.name.replace(u", jusqu'à", '')
            product.url = node.find_element_by_xpath('./url').text
            product.price = u'€' + node.find_element_by_xpath('./prix').text
            product.attributes.update({
                'direct_site_name': direct_site_name,
                'direct_site_image': direct_site_image,
            })
            products.append(product)
            images.append(node.find_element_by_xpath('./image').text)

        # stage 2 of VP scraping? load actual page
        print('loading url ' + url)
        for page in [url, url + '?p=2']:  # hack, gets pages 1 and 2
            self.driver.get(page)
            print('loaded url ' + page)

            # for faster traversal ops
            page_str = self.driver.find_element_by_xpath('//*').get_attribute('outerHTML')

            for idx, product in enumerate(products):
                image = images[idx]

                if not str(product.sku) in page_str:
                    print "product {0} is not on the page; skipping".format(product.sku)
                    continue

                try:
                    # find the review for this product
                    review_el = self.driver.find_element_by_xpath(
                            '//div'
                            '/div[contains(@class, "viewp-product-editorialist-{0}")]'
                            '/blockquote'.format(product.sku))
                    review_text = review_el.text or review_el.get_attribute('innerHTML')
                    product.attributes.update({"review_text": review_text})
                    print "Saved product {0} with review found".format(product.sku)
                    product.save()
                except NoSuchElementException:
                    print "No review was found for product {0}".format(product.sku)

                try:
                    # all 'products' have a link inside that contains the sku
                    item = self.driver.find_element_by_xpath('//div[contains(div/h2/a/@href, "/{0}/")]'.format(product.sku))
                    product.default_image = self._process_image(image, product)
                    product.save()
                except NoSuchElementException:
                    print "product {0} is not on this page".format(product.sku)

                try:
                    # type unicode
                    all_image_urls = [x.get_attribute('data-original') for x in
                                      self.driver.find_elements_by_xpath(
                            '//div/figure/div[@data-id="{0}"]//li/a/img'.format(
                                product.sku))]
                    if all_image_urls:
                        print "Adding more image urls to product: {0}".format(
                            all_image_urls)

                        product.product_images = [
                            self._process_image(image_url, product)
                            for image_url in all_image_urls
                        ]
                    else:
                        print "? found product on the page, but it had no images"
                except NoSuchElementException:
                    print "product images not found on the page"
                    continue

                product.save()
                yield {'product': product}
