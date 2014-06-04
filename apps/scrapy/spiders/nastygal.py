from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from urlparse import urlparse
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class NastyGalSpider(SecondFunnelScraper, WebdriverCrawlSpider):
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

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_product(self, response):
        sel = Selector(response)

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', '.product-style::text', re='Style #:(\d+)')
        l.add_css('name', 'h1.product-name::text')
        l.add_css('price', '.current-price::text', re='\$(.*)')
        l.add_value('in_stock', True)

        l.add_css('description', '.product-description')
        l.add_css('image_urls', '.carousel img::attr(src)')

        # Handle categories
        breadcrumbs = iter(sel.css('.breadcrumb a'))
        breadcrumb = next(breadcrumbs)  # Skip the first element

        categories = []
        for breadcrumb in breadcrumbs:
            category_name = breadcrumb.css('span::text').extract_first().strip()
            category_url = breadcrumb.css('::attr(href)').extract_first()

            categories.append((
                category_name,
                hostname + category_url
            ))

        attributes = {}
        attributes['categories'] = categories
        l._add_value('attributes', attributes)

        yield l.load_item()
