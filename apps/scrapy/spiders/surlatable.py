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
        is_product_page = re.search('(\d+)', response.url)
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

        # http://doc.scrapy.org/en/latest/topics/loaders.html#scrapy.contrib.loader.ItemLoader.add_value
        l.add_value("sku", response.url, re='(\d+)')
        sku = l.get_output_value("sku")

        l.add_css('name', 'h1.name::text')

        # TODO: Sanitize output with bleach
        l.add_css('description', '#description span.boxsides')

        attributes = {}

        try:
            sale_price = sel.css('li.sale::text')[1].extract().strip()
            price = sel.css('li.regular::text')[0].extract().replace('\n', '').replace('\t', '').replace('Was:', '')
            attributes['sale_price'] = sale_price
        except IndexError:
            price = sel.css('li.price::text')[-1].extract().replace('\n', '').replace('\t', '')

        # some variable-price like "$10 - $20"...
        if '-' in price:
            price = price[:price.index("-")].strip()

        l.add_value('price', price)

        # TODO: more Image URLs
        image_urls = [
            # this is unfortunately reverse-engineered (and 1079 seems to be a magic number)
            "http://www.surlatable.com//images/customers/c1079/PRO-{sku}/PRO-{sku}_detail/main_variation_Default_view_1_426x426.jpg".format(sku=sku)
        ]
        l.add_value('image_urls', image_urls)

        l.add_value('attributes', attributes)

        yield l.load_item()
