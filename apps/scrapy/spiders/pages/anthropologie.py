from urlparse import urlparse

from scrapy.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spiders import Rule
from scrapy.selector import Selector

from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class AnthropologieSpider(SecondFunnelCrawlSpider):
    name = 'anthropologie'
    allowed_domains = ['anthropologie.com']
    start_urls = ['http://www.anthropologie.com/']
    rules = [
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "next")]')
        ),
        Rule(
            SgmlLinkExtractor(allow=[
                r'/anthro/product/.+'
            ]),
            'parse_product', follow=False
        )
    ]

    store_slug = name

    def __init__(self, *args, **kwargs):
        super(AnthropologieSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.size-dropdown')

        return is_product_page


    def parse_product(self, response):
        """
        Parses a product page on Anthropologie.com.

        @url http://www.anthropologie.com/anthro/product/accessories-jewelry/32478539.jsp#/
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
        l.add_css('price', '.product-info .price', re=r'\$(.*)')
        l.add_value('in_stock', True)

        l.add_css('description', '.description-content')
        l.add_css('image_urls', '#imgSlider img::attr(ng-src)')

        # Handle tags
        breadcrumbs = iter(sel.css('.product-breadcrumb a'))
        breadcrumb = next(breadcrumbs)  # Skip the first element

        tags = []
        for breadcrumb in breadcrumbs:
            category_name = breadcrumb.css('::text').extract_first().strip()
            category_url = breadcrumb.css('::attr(href)').extract_first()

            tags.append((
                category_name,
                hostname + category_url
            ))

        attributes = {}
        attributes['tags'] = tags
        l.add_value('attributes', attributes)

        yield l.load_item()
