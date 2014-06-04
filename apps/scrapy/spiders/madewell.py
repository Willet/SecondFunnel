from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class MadewellSpider(SecondFunnelScraper, WebdriverCrawlSpider):
    name = 'madewell'
    allowed_domains = ['madewell.com']
    start_urls = ['http://www.madewell.com/']
    rules = [
        Rule(SgmlLinkExtractor(allow=[
            r'/\w+\d+.jsp'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name

    def __init__(self, *args, **kwargs):
        super(MadewellSpider, self).__init__(*args, **kwargs)

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_product(self, response):
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', '.item-num::text', re='item (\w+\d+)')
        l.add_css('name', 'h1::text')
        l.add_css('price', '.full-price span::text', re='USD (.*)')
        l.add_value('in_stock', True)

        l.add_css('description', '#prodDtlBody')
        l.add_css('image_urls', '.float-left img::attr(data-imgurl)')

        # Madewell categories are tricky

        yield l.load_item()
