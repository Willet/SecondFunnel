import re

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from apps.assets.models import Image, Product, Store

from apps.scraper.models import Scraper, ProductDetailScraper, ProductCategoryScraper, ContentDetailScraper


class GapProductScraper(ProductDetailScraper):
    store = Store.objects.get(slug='gap')
    regexs = [Scraper._wrap_regex(r'(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*', True)]
    sku_regex = r'^http://www\.gap\.com/browse/product\.do\?pid=(\d{6})$'
    imageLabels = ["Z", "AV1_Z", "AV2_Z", "AV9_Z", "SC_OUT_Z"]

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/product.do?pid=' + re.match(self.regexs[0], url).group(1)

    def parse(self, url, values, **kwargs):
        product = kwargs.get('product')
        url = self._wrap_url(url)
        print('loading ' + url)
        page_source, page = self.scrape(url=url)

        try:
            product.name = page.select('span.productName')[0].text
        except IndexError:  # only pages with ^ is in stock
            product.in_stock = False
            product.save()
            yield {'product': product}
            return

        # retrieve the price of the product
        try:
            # TODO: For scraping gap, span#priceText can contain both the original price and the sale price
            product.price = page.select('span#priceText strike')[0].text
        except IndexError:  # original price not found; guess
            try:
                product.price = page.select('#priceText')[0].text
            except:
                pass

        # retrieve the sale price of the product
        try:
            sale_price = page.select('span.salePrice')[0].text
            product.attributes.update({'sale_price': sale_price})
        except IndexError:
            try:
                sale_price_text = page.select('#productPageMupMessageStyle')[0].text
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
            category_url = category_elem.get_attribute('href')
            if category_url.startswith('/'):
                category_url = 'http://www.gap.com' + category_url
            # using innerHTML because category_elem.text does not seem to work here
            category_name = category_elem.get_attribute('innerHTML').replace('<p>', '').replace('</p>', '')
            if category_name == 'body' or category_name == 'gapfit' or category_name == 'maternity':
                self._add_to_category(product, 'women', 'http://www.gap.com/browse/subDivision.do?cid=5646')
            else:
                self._add_to_category(product, category_name, category_url)
        except IndexError:
            pass

        if values.get('category', None):
            self._add_to_category(product, values.get('category', None))
        if values.get('sub_category', None):
            self._add_to_category(product, values.get('sub_category', None))

        # given a url, scrape some other url (the same product's data json)
        page_source, page = self.scrape('http://www.gap.com/browse/productData.do?pid=%s' % product.sku)

        images = self._get_images(page_source, product)
        if len(images) > 0:
            product.default_image = images[0]
            product.save()

        yield {'product': product}

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
                if name in self.imageLabels:
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
    regexs = [Scraper._wrap_regex(r'(?:www\.)?gap\.com/browse/category\.do\?[^/\?]*cid=(\d*)', True)]
    product_sku_regex = r'^(?:(?:https?://)?(?:www\.)?gap\.com)?/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&[^/\?]*)?$'

    def parse_url(self, url, **kwargs):
        return 'http://www.gap.com/browse/category.do?cid=' + re.match(self.regexs[0], url).group(1)

    def parse(self, url, values, **kwargs):
        page_source, page = self.scrape(url)

        # get category name
        try:
            values['category'] = page.select('span#subcatname')[0].text.strip()
        except IndexError:
            pass

        # get number of pages
        try:
            page_text = page.select('label.pagePaginatorLabel')[0].text
            if page_text:
                pages = int(re.match(r'Page *\d+ *of *(\d+)', page_text).group(1))
            else:
                pages = 1
        except IndexError:
            pages = 1

        page_num = 0
        while page_num < pages:
            page_source, page = self.scrape(url + '#pageId=' + str(page_num))

            # get all sub categories on the page
            try:
                sub_categories = page.select('div#mainContent div.clearfix h2')
            except NoSuchElementException:
                sub_categories = []

            product_groups = page.select('div#mainContent div.clearfix ul')

            for i in range(len(product_groups)):
                if sub_categories:
                    values['sub_category'] = sub_categories[i].text
                else:
                    values['sub_category'] = None
                for product_elem in product_groups[i].select('li div a'):
                    href = product_elem.get_attribute('href')
                    match = re.match(self.product_sku_regex, href)
                    if match:
                        sku = match.group(1)
                        product_url = 'http://www.gap.com/browse/product.do?pid=' + sku
                        name = product_elem.find_element_by_xpath('.//img').get_attribute('alt')

                        product = self._get_product(product_url)
                        product.sku = sku
                        product.name = name
                        yield {'product': product, 'url': product_url}
                    else:
                        # if item is not a product, check if it is a STL
                        match = re.match(STLScraper.regexs[0], href)
                        if match:
                            yield {'url': href}
                        else:
                            pass
            page_num += 1


class STLScraper(ContentDetailScraper):
    store = Store.objects.get(slug='gap')
    regexs = [Scraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?(?:[^/\?]*&)*cid=(\d+)(?:&[^/\?]*)*&oid=(OUT-\d+)', True),
              Scraper._wrap_regex('(?:www\.)?gap.com/browse/outfit\.do\?(?:[^/\?]*&)*oid=(OUT-\d+)(?:&[^/\?]*)*&cid=(\d+)', True)]

    def parse_url(self, url, **kwargs):
        match = re.match(self.regexs[0], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={0}&oid={1}'.format(match.group(1), match.group(2))
        match = re.match(self.regexs[1], url)
        if match:
            return 'http://www.gap.com/browse/outfit.do?cid={1}&oid={0}'.format(match.group(1), match.group(2))

    def scrape(self, url, **kwargs):
        print('loading url ' + url)
        self.driver.get(url)
        print('url loaded')
        outfit_content = self.driver.find_element_by_xpath('//div[@id="outfitContent"]')
        image_url = outfit_content.find_element_by_xpath('./div[@id="outfitContentLeft"]/div[@id="outfitImages"]//img').get_attribute('src')
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
                                         self.driver.page_source):
            sku = product_match.group(1)
            try:
                product = Product.objects.get(store=self.store, sku=sku)
                image.tagged_products.add(product)
            except Product.DoesNotExist:
                yield {'url': 'http://www.gap.com/browse/product.do?pid=' + sku}
                product = Product.objects.get(store=self.store, sku=sku)
                image.tagged_products.add(product)
                pass
        yield {'content': image}
