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
        store = self.store
        products = []
        images = []
        skus = []  # list of product skus that are in the feed (which may or may not be in status (statut) 1
        print('loading url http://www.officiel-des-vacances.com/partners/catalog.xml')
        self.driver.get('http://www.officiel-des-vacances.com/partners/catalog.xml')
        print('url loaded')
        for node in self.driver.find_elements_by_xpath('//nodes/node'):
            sku = node.find_element_by_xpath('./id').text
            skus.append(sku)
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
            product.name = product.name.replace(u"jusqu'à", '')
            product.name = product.name.strip(' ,')  # remove spaces, commas, ...

            product.url = node.find_element_by_xpath('./url-detail').text
            product.price = u'€' + node.find_element_by_xpath('./prix').text

            # this is the default
            product.in_stock = (node.find_element_by_xpath('./statut').text is '1')

            product.attributes.update({
                'direct_site_name': direct_site_name,
                'direct_site_image': direct_site_image,
            })
            products.append(product)
            images.append(node.find_element_by_xpath('./image').text)

        # after-the-fact processing
        for product in Product.objects.filter(store=store):
            # mark all products not in feed as 'not in stock'
            if product.in_stock and not product.sku in skus:
                print "Product {0} no longer in stock!".format(product.sku)
                product.in_stock = False
                product.save()

            if u"jusqu'à" in product.name:
                product.name = product.name.replace(u"jusqu'à", '')
                product.save()

        # stage 2 of VP scraping? load actual page
        print('loading url ' + url)
        for page in [url, url + '?p=2']:  # hack, gets pages 1 and 2
            self.driver.get(page)
            print('loaded url ' + page)

            # for faster traversal ops
            page_str = self.driver.find_element_by_xpath('//*').get_attribute('outerHTML')

            for idx, product in enumerate(products):
                image = images[idx]
                if image:  # save paired default image
                    product.save()
                    try:
                        product.default_image = self._process_image(image, product)
                    except Exception as err:
                        print "PV image CDN died"

                # if product is on the page, provide product with extra information
                # like images and reviews
                if str(product.sku) in page_str:
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

                    try:  # type unicode
                        all_image_urls = [x.get_attribute('data-original') for x in
                                          self.driver.find_elements_by_xpath(
                                '//div/figure/div[@data-id="{0}"]//li/a/img'.format(
                                    product.sku))]
                        if all_image_urls:
                            print "Adding more image urls to product: {0}".format(
                                all_image_urls)

                            product.product_images.clear()
                            for image_url in all_image_urls:
                                try:
                                    product.product_images.add(
                                        self._process_image(image_url, product))
                                except Exception as err:
                                    print "PV image CDN died"

                        else:
                            print "? found product on the page, but it had no images"
                    except NoSuchElementException:
                        print "product images not found on the page"
                        continue

                product.save()
                yield {'product': product}
