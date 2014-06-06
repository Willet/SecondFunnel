import re
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider,\
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class SurlatableSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'surlatable'
    allowed_domains = ['surlatable.com']
    start_urls = []
    rules = [
        Rule(SgmlLinkExtractor(allow=[r'.*product/PRO-.*']),
             callback='parse_product',
             follow=False)
    ]

    store_slug = name

    def is_product_page(self, response):
        is_product_page = re.search('.*product/PRO-.*', response.url)
        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on SurLaTable.com.

        @url http://www.surlatable.com/product/PRO-1447598/Fish+Individual+Bowl
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price description image_urls attributes
        """

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', response.url)
        l.add_css('name', 'h1.name::text')
        l.add_css('description', '#description span.boxsides')
        l.add_value("sku", response.url, re='(\d+)')

        attributes = {}

        sale_price = sel.css('li.sale::text').re_first('(\$\d+\.\d+)')

        if sale_price:
            attributes['sale_price'] = sale_price
            l.add_css('price', 'li.regular::text', re='(\$\d+\.\d+)')
        else:
            l.add_css('price', 'li.price::text', re='(\$\d+\.\d+)')

        # TODO: more Image URLs
        image_urls = [
            # this is unfortunately reverse-engineered (and 1079 seems to be a magic number)
            "http://www.surlatable.com//images/customers/c1079/PRO-{sku}/PRO-{sku}_detail/main_variation_Default_view_1_426x426.jpg".format(
                sku=l.get_output_value("sku")
            )
        ]

        l.add_value('image_urls', image_urls)
        l.add_value('attributes', attributes)

        yield l.load_item()
