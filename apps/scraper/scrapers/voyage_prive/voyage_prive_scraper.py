# coding=utf-8
import re

from apps.assets.models import Page, Product

from apps.scraper.scrapers import ProductCategoryScraper
from selenium.common.exceptions import NoSuchElementException


class VoyagePriveCategoryScraper(ProductCategoryScraper):
    regexs = ['https?://www.officiel-des-vacances.com/week-end']

    def parse_url(self, **kwargs):
        return 'http://www.officiel-des-vacances.com/week-end'

    def scrape(self, url, **kwargs):
        """Scrapes Voyage Prive.

        In addition to scraping products from the store, this scraper adds
        and removes products from the 'week-end' page.
        """
        store = self.store
        page = store.pages.filter(url_slug='week-end')[0]
        feed = page.feed
        # pre-sized cdn image
        image_url_gex = re.compile(r'(^https?://)?(www\.)?cdn\.officiel-des-vacances\.com/files/styles/product_\d+x\d+/public/product/(\w+\.jpg.*)')

        products = []
        images = []
        skus = []  # list of product skus that are in the feed (which may or may not be in status (statut) 1
        print('loading url http://www.officiel-des-vacances.com/partners/catalog.xml')
        self.driver.get('http://www.officiel-des-vacances.com/partners/catalog.xml')
        print('url loaded')
        for node in self.driver.find_elements_by_xpath('//nodes/node'):
            sku = node.find_element_by_xpath('./id').text
            skus.append(sku)

            try:
                if not u'10033' in [x.strip() for x in node.find_element_by_xpath('./sections').text.split(',')]:
                    continue  # this product is not a week-end trip
            except (AttributeError, NoSuchElementException):
                continue  # no 'sections'

            direct_site_name = node.find_element_by_xpath('./nom-fournisseur').text
            direct_site_image = node.find_element_by_xpath('./image-fournisseur').text
            try:
                product = Product.objects.filter(sku=sku)[0]
            except (Product.DoesNotExist, IndexError):
                product = Product(sku=sku)
            product.store = self.store
            product.name = node.find_element_by_xpath('./titre').text
            match = re.match(r"""(.+),?         # Name of product
                                 \s*            # Followed by 0 or more spaces
                                 (-\s*\d+%)     # Percentage of product off
                              """, product.name, re.VERBOSE)
            if match:
                product.name = match.group(1).strip()
                product.attributes['discount'] = match.group(2)

            # in no position of the product name is 'jusqu'à' a useful term to keep
            product.name = product.name.replace(u"jusqu'à", '')
            product.name = product.name.replace(u"jusqu’à", '')

            product.name = product.name.strip(' ,')  # remove spaces, commas, ...

            # we want a special url format;
            # see https://github.com/Willet/SecondFunnel/pull/720#issuecomment-41426543
            product.url = 'http://www.officiel-des-vacances.com/' \
                          'route-to/{0}/section'.format(sku)
            product.price = u'€' + node.find_element_by_xpath('./prix').text

            # this is the default
            product.in_stock = (node.find_element_by_xpath('./statut').text
                                in [1, '1', u'1'])

            product.attributes.update({
                'direct_site_name': direct_site_name,
                'direct_site_image': direct_site_image,
            })
            products.append(product)

            image_url = node.find_element_by_xpath('./image').text
            match = image_url_gex.match(image_url)
            if match:  # convert to full-size image if...
                image_url = 'http://cdn.officiel-des-vacances.com/files/product/{0}'.format(match.groups()[2])
            images.append(image_url)

        # after-the-fact processing
        for product in Product.objects.filter(store=store):
            # mark all products not in feed as 'not in stock'
            if product.in_stock and not product.sku in skus:
                print "Product {0} no longer in stock!".format(product.sku)
                product.in_stock = False
                product.save()
                feed.remove_product(product)

            if u"jusqu'à" in product.name or u"jusqu’à" in product.name:
                product.name = product.name.replace(u"jusqu'à", '')
                product.name = product.name.replace(u"jusqu’à", '')
                product.name = product.name.strip(' ,')  # remove spaces, commas, ...
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
                if not image:
                    # XML didn't have an image for this product
                    print "Product {0} does not have an image!".format(
                        getattr(product, 'sku', 0))
                    try:
                        product.delete()
                    except AssertionError:
                        pass  # not in DB yet; this product will be skipped
                    continue

                # save paired default image
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

                        reviewer_el = self.driver.find_element_by_xpath(
                                '//div'
                                '/div[contains(@class, "viewp-product-owner-{0}")]'
                                '/a'.format(product.sku))
                        reviewer_name = reviewer_el.text or reviewer_el.get_attribute('innerHTML')

                        reviewer_img_el = self.driver.find_element_by_xpath(
                                '//div'
                                '/div[contains(@class, "viewp-product-editorialist-{0}")]'
                                '/img'.format(product.sku))
                        reviewer_img = reviewer_img_el.get_attribute('src')

                        product.attributes.update({
                            "review_text": review_text,
                            "reviewer_name": reviewer_name,
                            "reviewer_image": reviewer_img,
                        })
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

                            # rebuild product images list
                            for img in product.product_images.all():
                                img.product = None
                                img.save()
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

                # add a tile to the weekend feed
                try:
                    tile, p, _ = feed.add_product(product)
                    tile.template = 'banner'
                    tile.save()
                except Exception as err:
                    pass  # let other products be processed

                yield {'product': product}
