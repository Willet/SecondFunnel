import re
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.utils.misc import open_in_browser


class SurlatableSpider(WebdriverCrawlSpider):
    name = 'surlatable'
    allowed_domains = ['surlatable.com', 'www.surlatable.com']
    start_urls = ['http://www.surlatable.com/category/cat450428/Le-Creuset',
                  'http://www.surlatable.com/category/cat850441/Le-Creuset-Stoneware',
                  'http://www.surlatable.com/category/cat450481/Le-Creuset',
                  'http://www.surlatable.com/category/cat450610/Le-Creuset' ]
    rules = [
        Rule(SgmlLinkExtractor(allow=[r'.*product/PRO-.*']),
             callback='parse_product',
             follow=False)
    ]

    store_slug = name

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_product(self, response):

        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', response.url)

        sku = re.findall(r'(\d+)',response.url)[0]
        l.add_value('sku', sku)

        l.add_css('name', 'h1.name::text')

        # TODO: Sanitize output with bleach
        l.add_value('description', sel.css('#description span.boxsides').extract_first())

        # TODO: Image URLs
        image_urls = []

        attributes = {}

        try:
            sale_price = sel.css('li.sale::text')[1].extract().strip()
            price = sel.css('li.regular::text')[0].extract().replace('\n', '').replace('\t', '').replace('Was:', '')
            attributes['sale_price'] = sale_price
        except IndexError:
            price = sel.css('li.price::text')[0].extract().replace('\n', '').replace('\t', '')

        l.add_value('price', price)

        # TODO: Monday
        attributes['categories'] = []
        category_sels = sel.css('.breadcrumbs').xpath('a[@href!="#"]')
        for category_sel in category_sels:
            category_url = category_sel.css('::attr(href)').extract_first()
            category_name = category_sel.css('::text').extract_first().strip()
            attributes['categories'].append((category_name, category_url))

        l.add_value('image_urls', image_urls)
        l.add_value('attributes', attributes)

        yield l.load_item()
