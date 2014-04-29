import re

from selenium.common.exceptions import NoSuchElementException
from apps.assets.models import Store

from apps.scraper.models import Scraper, ProductDetailScraper, ProductCategoryScraper


class MadewellProductScraper(ProductDetailScraper):
    store = Store.objects.get(slug='madewell')
    regexs = [Scraper._wrap_regex(r'(?:www\.)?madewell\.com/madewell_category/(?:(\w+)/(?:(\w+)/)?)?PRD(?:OVR)?~(\w+)/\3\.jsp')]
    sku_regex = r'^http://www\.madewell\.com/madewell_category/PRDOVR~(\w+)/\1\.jsp$'

    def parse_url(self, url, values, **kwargs):
        """Transform a url to one that we will actually scrape."""
        match = re.match(self.regexs[0], url)
        url_base = 'http://www.madewell.com/madewell_category'
        url = '{0}/PRDOVR~{1}/{1}.jsp'.format(url_base, match.group(3))
        category = match.group(1)
        sub_category = match.group(2)

        if category:
            values['category'] = category
            values['category_url'] = '{0}/{1}.jsp'.format(url_base, category)
        if sub_category:
            values['sub_category'] = sub_category
            values['sub_category_url'] = '{0}/{1}/{2}'.format(
                url_base, category, sub_category)

        return url

    def process(self, url, page, text='', status=200, **kwargs):
        product = self.get_product(url=url)
        product.sku = re.match(self.regexs[0], product.url).group(3)

        try:
            product.price = re.sub(r'USD *', '$', page.select('.selected-color-price')[0].text)
        except NoSuchElementException:
            product.price = re.sub(r'USD *', '$', page.select('div.full-price span')[0].text)

        try:
            product.name = page.select('section.description header h1')[0].text
        except NoSuchElementException:
            product.name = page.select('section#description header h1')[0].text

        product.description = page.select('#prodDtlBody')[0].attrs.get("innerHTML")

        product.save()

        if kwargs.get('category', None):
            self._add_to_category(product, kwargs.get('category', None), kwargs.get('category_url'))
        if kwargs.get('sub_category', None):
            self._add_to_category(product, kwargs.get('sub_category', None), kwargs.get('sub_category_url'))

        images = self._get_images(page, product)
        if len(images) > 0:
            product.default_image = images[0]
            product.save()

        return {'product': product}

    def _get_images(self, page, product):
        """
        :param page  <BeautifulSoup>
        """
        images = []
        images_data = page.select('div.float-left img')
        if images_data:
            for img in images_data:
                image = img.get_attribute('data-imgurl')
                images.append(self._process_image(image, product))
        else:
            image = page.select('.prod-main-img')[0].attrs.get('src')
            images.append(self._process_image(image, product))

        if len(images) == 0:
            return images

        for image in product.product_images.exclude(id__in=[
            image.id for image in images]):
            print "Deleting expired image {0}".format(image)
            image.delete()

        return images


class MadewellCategoryScraper(ProductCategoryScraper):
    store = Store.objects.get(slug='madewell')
    regexs = [Scraper._wrap_regex(r'(?:www\.)?madewell\.com/madewell_category/(\w+)(?:/(\w+))?\.jsp')]

    def parse_url(self, url, values, **kwargs):
        """Transform a url to one that we will actually scrape."""
        match = re.match(self.regexs[0], url)
        category = match.group(1)
        sub_category = match.group(2)
        url = 'http://www.madewell.com/madewell_category/' + category
        values['category'] = category
        values['category_url'] = 'http://www.madewell.com/madewell_category/{0}.jsp'.format(category)
        if sub_category:
            url += '/' + sub_category
            values['sub_category'] = sub_category
            values['sub_category_url'] = 'http://www.madewell.com/madewell_category/{0}/{1}.jsp'.format(category, sub_category)
        url += '.jsp'
        return url

    def process(self, url, page, text='', status=200, **kwargs):
        products_data = page.select('td.arrayProdCell td.arrayImg a')
        for product_data in products_data:
            product_url = (MadewellProductScraper()
                           .parse_url(product_data.attrs.get('href'), {})
                           .get('url'))
            sku = re.match(MadewellProductScraper().sku_regex, url).group(3)
            name = product_data.select('img')[0].attrs.get('alt')

            product = self.get_product(url=product_url)

            product.name = name
            product.sku = sku

            print "[{0}] Saving product {1}".format(
                self.__class__.__name__, product)
            product.save()
            # return {'product': product, 'url': product_url}


class MadewellMultiProductScraper(ProductCategoryScraper):
    store = Store.objects.get(slug='madewell')
    regexs = [Scraper._wrap_regex(r'(?:www\.)?madewell\.com/browse/multi_product_detail.jsp\?(?:[^/\?]+&)?externalProductCodes=([^&\?/]+)', True)]

    def process(self, url, page, text='', status=200, **kwargs):
        product_codes = re.match(self.regexs[0], url).group(1)
        codes = re.split('%3A|:', product_codes)
        for sku in codes:
            if sku == '00000':
                continue
            url_base = 'http://www.madewell.com/madewell_category'
            product_url = '{0}/PRDOVR~{1}/{1}.jsp'.format(url_base, sku)

            product = self.get_product(url=product_url)
            product.sku = sku

            print "[{0}] Saving product {1}".format(
                self.__class__.__name__, product)
            product.save()
            # return {'product': product, 'url': product_url}
