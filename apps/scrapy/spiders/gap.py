from urlparse import urljoin
from scrapy import log
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from experiment.scraper.items import ScraperProduct
from experiment.scraper.spiders.webdriver import WebdriverCrawlSpider

# TODO: Dupe checking
#   see http://doc.scrapy.org/en/latest/topics/settings.html?highlight=dupe#dupefilter-class
#   see http://doc.scrapy.org/en/latest/topics/item-pipeline.html#duplicates-filter
# TODO: Memory
from experiment.scraper.utils import open_in_browser
# Pagination


class GapSpider(WebdriverCrawlSpider):
    name = 'gap'
    allowed_domains = ['gap.com']
    # start_urls = ['http://www.gap.com/']
    start_urls = ['http://www.gap.com/browse/category.do?cid=65289']
    rules = [
        # Rule(SgmlLinkExtractor(allow=[
        #     r'\/browse\/subDivision.do\?.*?cid=\d+'
        # ]), 'parse_division'),
        # Rule(SgmlLinkExtractor(allow=[
        #     r'\/browse\/category.do\?.*?cid=\d+'
        # ]), 'parse_category'),
        Rule(SgmlLinkExtractor(allow=[
            r'/browse/product.do\?.*?pid=\d+'
        ]), 'parse_product')
    ]

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_division(self, response):
        sel = Selector(response)
        base_url = response.url

        divisions = sel.css('.category > a')

        for division in divisions:
            # TODO: Extract returns one-element list: how to avoid?
            url = division.css('::attr(href)').extract()[0].strip()
            text = division.css('::text').extract()[0].strip()
            msg = u'PARSE_DIVISION - {category}: {url}'.format(url=url,
                                                               category=text)
            log.msg(msg, level=log.DEBUG)

            yield WebdriverRequest(urljoin(base_url, url))

    def parse_category(self, response):
        sel = Selector(response)
        base_url = response.url

        products = sel.css('.productCatItem > a')

        for product in products:
            url = product.css('::attr(href)').extract()[0].strip()
            text = product.css('::text').extract()[0].strip()
            msg = u'PARSE CATEGORY - {product}: {url}'.format(url=url,
                                                              product=text)
            log.msg(msg, level=log.DEBUG)

            yield WebdriverRequest(urljoin(base_url, url))

    def parse_product(self, response):
        sel = Selector(response)

        item = ScraperProduct()
        item['image_urls'] = []
        item['store'] = self.name

        product_name = sel.css('#productNameText .productName::text').extract()
        if product_name:
            item['name'] = product_name[0]

        price = sel.css('#priceText::text').extract()\
            or sel.css('#priceText strike::text').extract()

        if price:
            item['price'] = price[0]

        # Mostly for proof of concept
        image = sel.css('#product_image_bg img::attr(src)').extract()
        if image:
            item['image_urls'].append(image[0])

        yield item