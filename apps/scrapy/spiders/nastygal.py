from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from urlparse import urlparse
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class NastyGalSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'nastygal'
    allowed_domains = ['nastygal.com']
    start_urls = ['http://www.nastygal.com/']
    rules = [
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "next")]')
        ),
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "product-link")]'),
            'parse_product', follow=False
        )
    ]

    store_slug = name

    def __init__(self, *args, **kwargs):
        super(NastyGalSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.product-style')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on NastyGal.com.

        @url http://www.nastygal.com/whats-new_clothes/after-party-short-and-sweet-top
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', '.product-style::text', re=r'Style #:(\d+)')
        l.add_css('name', 'h1.product-name::text')
        l.add_css('price', '.current-price::text', re=r'\$(.*)')
        l.add_value('in_stock', True)

        l.add_css('description', '.product-description')
        l.add_css('image_urls', '.carousel img::attr(src)')

        # Handle categories
        categories = sel.css('.breadcrumb a span::text').extract()[1:]  # Skip the first element

        attributes = {}
        attributes['categories'] = categories
        l.add_value('attributes', attributes)

        yield l.load_item()
