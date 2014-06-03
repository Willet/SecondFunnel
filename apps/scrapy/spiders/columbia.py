from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from urlparse import urlparse
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class ColumbiaSpider(SecondFunnelScraper, WebdriverCrawlSpider):
    name = 'columbia'
    allowed_domains = ['columbia.com']
    start_urls = ['http://www.columbia.com/']
    start_urls_separator = '|'
    rules = [
        Rule(SgmlLinkExtractor(allow=[
            r'/\w{2}\d+.*\.html'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name

    def __init__(self, *args, **kwargs):
        super(ColumbiaSpider, self).__init__(*args, **kwargs)

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_product(self, response):
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_value('sku', l.get_output_value('url'), re='/(\w{2}\d+),')
        l.add_css('name', '.product_title::text')
        # TODO: Add details
        # TODO: remove view details
        l.add_css('description', '.description')
        l.add_css('price', '.price-index.regprice::text')
        l.add_value('in_stock', True)

        image = sel.css('#flashcontent').re_first('image=([^&]+)&')
        l.add_value(
            'image_urls',
            'http://s7d5.scene7.com/is/image/{}?scl=1.1&fmt=jpeg'.format(image)
        )

        attributes = {}

        # Handle categories
        breadcrumbs = iter(sel.css('#nav-trail a'))
        breadcrumb = next(breadcrumbs)  # Skip the first element

        categories = []
        for breadcrumb in breadcrumbs:
            category_name = breadcrumb.css('::text').extract_first().strip()
            category_url = breadcrumb.css('::attr(href)').extract_first()

            categories.append((category_name, category_url))

        sale_price = sel.css('#member-price').extract_first()
        if sale_price:
            attributes['sale_price'] = sel.css('#member-price')\
                .extract_first().replace('Now ', '')

        attributes['categories'] = categories
        l.add_value('attributes', attributes)

        yield l.load_item()
