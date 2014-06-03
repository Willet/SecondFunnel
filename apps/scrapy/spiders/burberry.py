from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class BurberrySpider(SecondFunnelScraper, WebdriverCrawlSpider):
    name = 'burberry'
    allowed_domains = ['burberry.com']
    start_urls = ['http://www.burberry.com/']
    rules = [
        Rule(SgmlLinkExtractor(allow=[
            r'/.*-p\d+'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name

    category_url = 'http://www.gap.com/browse/category.do?cid={}'
    visited = []

    def __init__(self, *args, **kwargs):
        super(BurberrySpider, self).__init__(*args, **kwargs)

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_product(self, response):
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', '.product-id.section span::text')
        l.add_css('name', '.product-title-container h1::text')
        l.add_css('price', '.price-amount::text')
        l.add_css('description', '#description-panel ul')
        l.add_value('in_stock', True)
        l.add_css('image_urls', '.product_viewer li.product-image::attr(data-zoomed-src)')

        # Handle categories
        categories = []
        for level in [1, 2, 3]:
            category_sel = sel.css('.l-{level}-active'.format(level=level))
            category_name = category_sel.css('::text').extract_first()
            category_url = category_sel.css('::attr(href)').extract_first()
            categories.append((category_name, category_url))

        attributes = {}
        attributes['categories'] = categories
        l.add_value('attributes', attributes)

        yield l.load_item()
