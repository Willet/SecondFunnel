from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from urlparse import urlparse
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

    def __init__(self, *args, **kwargs):
        super(BurberrySpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        if self.is_product_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_product(response)

        return []

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.product-id.section span')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on Burberry.com.

        @url http://ca.burberry.com/mid-length-cotton-sateen-trench-coat-p45099611
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

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
            category_name = category_sel.css('::text').extract_first().strip()
            category_url = category_sel.css('::attr(href)').extract_first()

            categories.append((
                category_name,
                hostname + category_url
            ))

        attributes = {}
        attributes['categories'] = categories
        l.add_value('attributes', attributes)

        yield l.load_item()
