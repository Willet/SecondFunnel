import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from apps.assets.models import Image, Product, Store

from apps.scraper.models import ProductDetailScraper, ProductCategoryScraper, ContentDetailScraper


class GapProductScraper(ProductDetailScraper):
    store = Store.objects.get(slug='gap')
    regexs = [ProductDetailScraper._wrap_regex(r'(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*', True)]
    sku_regex = r'^http://www\.gap\.com/browse/product\.do\?pid=(\d{6})$'
    image_labels = ["Z", "AV1_Z", "AV2_Z", "AV9_Z", "SC_OUT_Z"]

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/product.do?pid=' + re.match(self.regexs[0], url).group(1)

    def process(self, url, page, text='', status=200, **kwargs):
        """
        page is the loaded product page
        """
        product = self.get_product(url=url)

        try:
            product.name = page.select('span.productName')[0].get_text()
        except IndexError:  # only pages with ^ is in stock
            product.in_stock = False
            product.save()

        # retrieve the price of the product
        try:
            # if #priceText strike exists, then the striked out price is the
            # regular price, and the .salePrice inside it is the sale price
            product.price = page.select('span#priceText strike')[0].text
        except IndexError:  # original price not found; guess
            try:
                product.price = page.select('#priceText')[0].text
            except:
                print "Could not retrieve pricing information"

        # retrieve the sale price of the product
        try:
            sale_price = page.select('span.salePrice')[0].get_text()
            product.attributes.update({'sale_price': sale_price})
        except IndexError:
            try:
                # attempt to find the sale price here instead (div may exist, but may be empty)
                sale_price_text = page.select('#productPageMupMessageStyle')[0].get_text()
                match = re.match(r'Now (\$\d+\.\d{2})', sale_price_text)
                if match:
                    sale_price = match.group(1)
                    product.attributes.update({'sale_price': sale_price})
                else:
                    product.attributes.pop('sales_price', None)
            except IndexError:
                product.attributes.pop('sales_price', None)

        product.sku = re.match(self.sku_regex, product.url).group(1)
        product.description = self._sanitize_html(str(page.select('#tabWindow')[0]))

        product.save()

        # retrieving the major category for the product
        try:
            category_elem = page.select('li a._selected')[0]
            category_url = category_elem.attrs.get('href')
            if category_url.startswith('/'):
                category_url = 'http://www.gap.com' + category_url
            # using innerHTML because category_elem.text does not seem to work here
            category_name = str(category_elem).replace('<p>', '').replace('</p>', '')
            if category_name == 'body' or category_name == 'gapfit' or category_name == 'maternity':
                self._add_to_category(product, 'women', 'http://www.gap.com/browse/subDivision.do?cid=5646')
            else:
                self._add_to_category(product, category_name, category_url)
        except IndexError:
            pass

        if kwargs.get('category', None):
            self._add_to_category(product, kwargs.get('category', None))
        if kwargs.get('sub_category', None):
            self._add_to_category(product, kwargs.get('sub_category', None))

        # given a url, scrape some other url (the same product's data json)
        _, _, page, _ = self.scrape(urls='http://www.gap.com/browse/productData.do?pid=%s' % product.sku)[0]

        images = self._get_images(str(page), product)
        if len(images) > 0:
            product.default_image = images[0]
            product.save()

        return {'product': product}

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
                if name in self.image_labels:
                    if url.startswith('/'):
                        url = 'http://www.gap.com' + url
                    images.append(self._process_image(url, product))

        if len(images) == 0:
            return images

        for image in product.product_images.exclude(id__in=[image.id for image in images]):
            image.delete()

        return images


class GapCategoryScraper(ProductCategoryScraper):
    store = Store.objects.get(slug='gap')
    regexs = [ProductCategoryScraper._wrap_regex(r'(?:www\.)?gap\.com/browse/category\.do\?[^/\?]*cid=(\d*)', True)]
    product_sku_regex = r'^(?:(?:https?://)?(?:www\.)?gap\.com)?/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&[^/\?]*)?$'

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/category.do?cid=' + re.match(self.regexs[0], url).group(1)

    def process(self, url, page, text='', status=200, **kwargs):
        product_urls = []
        # get category name
        try:
            # e.g. "Skirts"
            kwargs['category'] = page.select('span#subcatname')[0].text.strip()
            print "Category '{0}' found on {1}".format(kwargs['category'], url)
        except IndexError:
            print "No category found on {0}".format(url)

        # get number of pages
        try:
            # something like 'Page 1 of 1'
            page_text = page.select('label.pagePaginatorLabel')[0].text
            if page_text:
                page_count = int(re.match(r'Page *\d+ *of *(\d+)', page_text).group(1))
            else:
                page_count = 1
        except IndexError:
            page_count = 1

        page_num = 0
        while page_num <= page_count:
            _, status, page, _ = self.scrape(urls="%s#pageId=%s" % (url, page_num))[0]

            # get all sub categories on the page
            try:
                # [<h2 class="header4">Dresses &amp; Skirts</h2>,
                #  <h2 class="header4 subcategoryHeader">Sale: Dresses</h2>]
                #  v-- this looks like
                sub_categories = page.select('div#mainContent div.clearfix h2')
            except NoSuchElementException:
                sub_categories = []

            product_groups = [x for x in page.select('div#mainContent div.clearfix ul')
                              if not x.attrs.get('id')]

            for idx, sub_category in enumerate(product_groups):
                try:
                    if sub_categories:
                        kwargs['sub_category'] = sub_categories[idx].text
                    else:
                        kwargs['sub_category'] = None
                except IndexError:
                    pass

                # kwargs looks like {'category': u'Skirts', 'sub_category': u'Knee Length'}
                for product_elem in product_groups[idx].select('li div a'):
                    href = product_elem.attrs.get('href')
                    match = re.match(self.product_sku_regex, href)
                    if match:
                        sku = match.group(1)
                        product_url = 'http://www.gap.com' \
                                      '/browse/product.do?pid={0}'.format(sku)
                        name = product_elem.find('img').attrs.get('alt')

                        product = self.get_product(url=product_url)
                        product.sku = sku
                        product.name = name

                        # add product to detail batch
                        product_urls.append(product_url)

                        print "[{0}] Saving product {1}".format(
                            self.__class__.__name__, product)
                        product.save()
                        # return {'product': product, 'url': product_url}

                        if kwargs.get('category'):
                            self._add_to_category(product=product,
                                                  name=kwargs['category'],
                                                  url=url)
                        if kwargs.get('sub_category'):
                            self._add_to_category(product=product,
                                                  name=kwargs['sub_category'],
                                                  url=url)
                    else:
                        # if item is not a product, check if it is a STL
                        match = re.match(STLScraper.regexs[0], href)
                        if match:
                            self.subscrape(urls=href, page_scraper=STLScraper)
            page_num += 1

        # fire off detail scrapers for all of the products in this category
        return self.subscrape(urls=product_urls, page_scraper=GapProductScraper)


class STLScraper(ContentDetailScraper):
    store = Store.objects.get(slug='gap')
    regexs = [ContentDetailScraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?(?:[^/\?]*&)*cid=(\d+)(?:&[^/\?]*)*&oid=(OUT-\d+)', True),
              ContentDetailScraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?(?:[^/\?]*&)*oid=(OUT-\d+)(?:&[^/\?]*)*&cid=(\d+)', True)]

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={0}&oid={1}'.format(match.group(1), match.group(2))
        match = re.match(self.regexs[1], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={1}&oid={0}'.format(match.group(1), match.group(2))

    def process(self, url, page, text='', status=200, **kwargs):
        outfit_content = page.select('div#outfitContent')[0]
        image_url = outfit_content.select('div#outfitContentLeft div#outfitImages img').attrs.get('src')
        if image_url.startswith('/'):
            image_url = 'http://www.gap.com' + image_url
        try:
            image = Image.objects.get(store=self.store, original_url=url)
        except Image.DoesNotExist:
            image = Image(store=self.store, source_url=image_url)
        image = self._process_image(image_url, image)
        image.original_url = url
        image.source = 'gap-stl'
        image.save()
        for product_match in re.finditer('objGIDPageViewAdapter\.objGIDOutfit\.arrayProducts\.push\(\{strProductId:\s"(\d+)',
                                         str(page)):
            sku = product_match.group(1)
            try:
                product = Product.objects.get(store=self.store, sku=sku)
                image.tagged_products.add(product)
            except Product.DoesNotExist:
                # return {'url': 'http://www.gap.com/browse/product.do?pid=' + sku}
                product = Product.objects.get(store=self.store, sku=sku)
                image.tagged_products.add(product)
                pass
        return {'content': image}
