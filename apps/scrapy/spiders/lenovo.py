import re
import time

from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy.spider import Spider
from urlparse import urlparse

from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class LenovoSpider(SecondFunnelCrawlScraper):
    name = 'lenovo'
    allowed_domains = ['lenovo.com', 'shop.lenovo.com']
    start_urls = ['http://shop.lenovo.com/us/en/tablets/']
    rules = [
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "next")]')
        ),
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "button") and contains(@class, "shop") and contains(@class, "fluid")]'),
            'parse_product', follow=False
        )
    ]

    store_slug = 'lenovo'

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.cta')

        return is_product_page

    def parse(self, response):
        return self.parse_start_url(response)

    def parse_product(self, response):
        """
        Parses a product page on Lenovo.com.

        @url http://shop.lenovo.com/us/en/tablets/lenovo/yoga-tablet-series/
        @returns items 1 10
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        url = response.url
        # hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        skus = (sel.css('meta[name="SKU"]::attr(content)').extract_first().split(','))
        first_sku = skus[0]
        l.add_value('sku', first_sku)

        product_name = u"{} {} {}".format(
            sel.css('meta[name="ProductName"]::attr(content)').extract_first(),
            sel.css('meta[name="ModelName"]::attr(content)').extract_first(),
            sel.css('meta[name="ModelNumber"]::attr(content)').extract_first())
        l.add_value('name', product_name)

        l.add_css('price', 'meta[itemprop="price"]::attr(content)')

        l.add_value('in_stock', True)

        l.add_css('description', '#features div div div.grid_8.alpha')
        l.add_css('details', '#highlights ul')

        image_urls = sel.css('figure:not([itemprop="video"]) a::attr(href)').extract()
        image_urls = [urlparse(url, scheme='http').geturl() for url in image_urls]
        l.add_value('image_urls', image_urls)

        yield l.load_item()
