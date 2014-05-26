import re
from urlparse import urljoin
from scrapy import log
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider

# TODO: Dupe checking
#   see http://doc.scrapy.org/en/latest/topics/settings.html?highlight=dupe#dupefilter-class
#   see http://doc.scrapy.org/en/latest/topics/item-pipeline.html#duplicates-filter
# TODO: Memory
# Pagination



class GapSpider(WebdriverCrawlSpider):
    name = 'gap'
    allowed_domains = ['gap.com']
    start_urls = ['http://www.gap.com/']
    rules = [
        # Rule(SgmlLinkExtractor(allow=[
        #     r'\/browse\/subDivision.do\?.*?cid=\d+'
        # ]), 'parse_division'),
        # Rule(SgmlLinkExtractor(allow=[
        #     r'\/browse\/category.do\?.*?cid=\d+'
        # ]), 'parse_category'),
        Rule(SgmlLinkExtractor(allow=[
            r'/browse/product.do\?.*?pid=\d+'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name

    # TODO: Handle 'styles'
    category_url = 'http://www.gap.com/browse/category.do?cid={}'

    def __init__(self, *args, **kwargs):
        super(GapSpider, self).__init__()

        if kwargs.get('categories'):
            categories = kwargs.get('categories').split(',')
            self.start_urls = [self.category_url.format(c) for c in categories]

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_division(self, response):
        sel = Selector(response)
        base_url = response.url

        divisions = sel.css('.category > a')

        for division in divisions:
            url = division.css('::attr(href)').extract_first().strip()
            text = division.css('::text').extract_first().strip()
            msg = u'PARSE_DIVISION - {category}: {url}'.format(url=url,
                                                               category=text)
            log.msg(msg, level=log.DEBUG)

            yield WebdriverRequest(urljoin(base_url, url))

    def parse_category(self, response):
        sel = Selector(response)
        base_url = response.url

        products = sel.css('.productCatItem > a')

        for product in products:
            url = product.css('::attr(href)').extract_first().strip()
            text = product.css('::text').extract_first().strip()
            msg = u'PARSE CATEGORY - {product}: {url}'.format(url=url,
                                                              product=text)
            log.msg(msg, level=log.DEBUG)

            yield WebdriverRequest(urljoin(base_url, url))

    def parse_product(self, response):
        sel = Selector(response)

        item = ScraperProduct()
        item['attributes'] = {}
        item['image_urls'] = []
        item['store'] = self.name

        url = response.url
        item['url'] = url

        sku = sel.css('link[rel="canonical"]::attr(href)').\
            re_first('/P(\d+).jsp')
        if sku:
            item['sku'] = sku

        product_name = sel.css('.productName::text')\
            .extract_first()

        # Presence of product name determines product availability
        if product_name:
            item['name'] = product_name
            item['in_stock'] = True
        else:
            item['in_stock'] = False

        description = sel.css('#tabWindow').extract_first()
        if description:
            item['description'] = description

        sale_price = sel.css('#priceText .salePrice::text').extract_first()

        if not sale_price:
            price = sel.css('#priceText::text').extract_first()
        else:
            price = sel.css('#priceText strike::text').extract_first()
            item['attributes']['sales_price'] = sale_price

        if price:
            item['price'] = price

        category_sel = sel.css('li a[class*=selected]')
        category_url = category_sel.css('::attr(href)').extract_first()
        category_name = category_sel.css('::text').extract_first()

        item['attributes']['categories'] = []
        item['attributes']['categories'].append((category_name, category_url))

        # Mostly for proof of concept
        image = sel.css('#product_image_bg img::attr(src)').extract_first()
        if image:
            item['image_urls'].append(image)

        yield item
