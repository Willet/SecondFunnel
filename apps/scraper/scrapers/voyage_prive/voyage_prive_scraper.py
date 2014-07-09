# coding=utf-8
import re

from django.conf import settings
from selenium.common.exceptions import NoSuchElementException

from apps.assets.models import Product
from apps.scraper.scrapers import ProductCategoryScraper
from apps.scraper.scrapers.scraper import ScraperException


class VoyagePriveCategoryScraper(ProductCategoryScraper):
    feed = None  # subclasses will assign this variable
    section_id = ''  # optional
    category_name = ''  # if present, adds products to a category by this name

    def scrape(self, url, **kwargs):
        """Scrapes Voyage Prive.

        In addition to scraping products from the store, this scraper adds
        and removes products from the 'week-end' page.
        """
        # pre-sized cdn image
        image_url_gex = re.compile(r'(^https?://)?(www\.)?cdn\.officiel-des-vacances\.com/files/styles/product_\d+x\d+/public/product/(\w+\.jpg.*)')

        products = []
        images = []
        skus = []  # list of week-end product skus that are in the feed (which may or may not be in status (statut) 1
        print('loading url http://www.officiel-des-vacances.com/partners/catalog.xml')
        self.driver.get('http://www.officiel-des-vacances.com/partners/catalog.xml')
        print('url loaded')
        product_nodes = self.driver.find_elements_by_xpath('//nodes/node')
        if not product_nodes:  # VP servers exploding
            raise ScraperException("Could not retrieve latest VP product info; aborting scraper")

        for node in product_nodes:
            sku = node.find_element_by_xpath('./id').text

            try:
                section_ids = node.find_element_by_xpath('./sections').text
                if self.section_id and not self.section_id in section_ids:
                    continue  # we don't scrape this section (category)
            except (AttributeError, NoSuchElementException):
                continue  # no 'sections'

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

        page_products = self.store.products.all()

        # after-the-fact processing
        for product in page_products:
            # mark all products not in feed as 'not in stock'
            if product.in_stock and not product.sku in skus:
                print "Product {0} no longer in stock!".format(product.sku)
                product.in_stock = False
                product.save()

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
                        print "Found review for product {0}".format(product.sku)
                    except NoSuchElementException:
                        print "No review was found for product {0}".format(product.sku)

                    try:
                        # find the bullet point details for this product
                        details = self.driver.find_element_by_xpath(
                            '//div'
                            '/div[contains(@viewp-connect, "{0}")]'
                            '//ul[@class="viewp-product-bullet-items"]'.format(
                                product.sku)).get_attribute('outerHTML')

                        product.details = self._sanitize_html(details)
                        print "Found details for product {0}".format(product.sku)
                    except NoSuchElementException:
                        print "No review was found for product {0}".format(product.sku)

                    try:  # type unicode
                        product.save()
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

                # currently assume all products are for this page
                if self.category_name:
                    self._add_to_category(product, name=self.category_name)

                if self.feed:
                    # add a tile to the feed
                    if product.in_stock:
                        tile, p, _ = self.feed.add_product(product)
                        tile.template = 'banner'
                        tile.save()
                    else:
                        # if it's out, remove it; if it's not out,
                        self.feed.remove_product(product)

                yield {'product': product}


class VoyagePriveWeekEndScraper(VoyagePriveCategoryScraper):
    """Allocates a specific feed to the parent scraper, so it knows
    where to auto-add products.
    """
    regexs = ['https?://www.officiel-des-vacances.com/week-end/?']
    section_id = u'10033'
    category_name = 'week-end'  # coincidentally same as the page name

    def __init__(self, store, feed=None):
        super(VoyagePriveWeekEndScraper, self).__init__(store=store, feed=feed)
        self.feed = self.store.pages.filter(url_slug='week-end')[0].feed


class VoyagePriveSejourScraper(VoyagePriveCategoryScraper):
    """Allocates a specific feed to the parent scraper, so it knows
    where to auto-add products.
    """
    regexs = ['https?://www.officiel-des-vacances.com/sejour/?']
    section_id = u'10029'
    category_name = 'sejour'  # coincidentally same as the page name

    def __init__(self, store, feed=None):
        super(VoyagePriveSejourScraper, self).__init__(store=store, feed=feed)
        self.feed = self.store.pages.filter(url_slug='sejour')[0].feed
