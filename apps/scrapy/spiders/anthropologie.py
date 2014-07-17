from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from urlparse import urlparse
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class AnthropologieSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'anthropologie'
    allowed_domains = ['anthropologie.com']
    start_urls = ['http://www.anthropologie.com/']
    rules = [
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "next")]')
        ),
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//div[contains(@class, "item-description")]/a[contains(@class, "product-link")]'),
            'parse_product', follow=False
        )
    ]

    store_slug = 'nasty-gal'

    def __init__(self, *args, **kwargs):
        super(AnthropologieSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.size-dropdown')

        return is_product_page


    def parse_product(self, response):
        """
        Parses a product page on Anthropologie.com.

        @url http://www.anthropologie.com/whats-new_clothes/after-party-short-and-sweet-top
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', '#styleno::text')
        l.add_css('name', 'h1.product-name::text')
        l.add_css('price', '.product-info .price::text', re='\$(.*)')
        l.add_value('in_stock', True)

        l.add_css('description', '.description-content::text')
        l.add_css('image_urls', '#imgSlider img::attr(data-zoomsrc)')

        # Handle categories
        breadcrumbs = iter(sel.css('.product-breadcrumb'))
        breadcrumb = next(breadcrumbs)  # Skip the first element

        categories = []
        for breadcrumb in breadcrumbs:
            if breadcrumb.css('a'):
                category_name = breadcrumb.css('a::text').extract_first().strip()
                category_url = breadcrumb.css('a::attr(href)').extract_first()

            categories.append((
                category_name,
                hostname + category_url
            ))

        attributes = {}
        attributes['categories'] = categories
        l.add_value('attributes', attributes)

        yield l.load_item()
