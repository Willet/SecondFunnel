from scrapy.selector import Selector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct

class SurLaTableSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'surlatable'
    root_url = "http://www.surlatable.com"
    allowed_domains = ['surlatable.com']
    store_slug = name

    # There is no way of making this pretty.  XPaths, my butt.
    rules = [
        Rule(SgmlLinkExtractor(restrict_xpaths=
            "//div[contains(@id, 'items')]/div[contains(@class, 'row')]/dl[contains(@class, 'item')]"
        ), callback="parse_product", follow=False)
    ]

    def __init__(self, *args, **kwargs):
        super(SurLaTableSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        return sel.css('label#productPriceValue')  # TODO: out-of-stock

    def parse_product(self, response):
        if not self.is_product_page(response):
            return

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        attributes = {}

        l.add_css('in_stock', True)
        l.add_css('name', 'h1.name::text')
        l.add_css('sku', '#productId::attr(value)', re=r'\d+')
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('description', '.boxsides::text')
        try:
            reg_price = sel.css('.regular label#productPriceValue::text').extract()[0]
        except IndexError:
            reg_price = sel.css('.price label#productPriceValue::text').extract()[0]
        else:
            attributes['sale_price'] = sel.css('.sale label#productPriceValue::text').extract()[0]
        l.add_value('price', reg_price.strip('$'))

        magic_values = sel.css('.fluid-display::attr(id)').extract_first().split(':')
        xml_path = '/images/customers/c{1}/{2}/{2}_{3}/pview_{2}_{3}.xml'.format(*magic_values)
        item = l.load_item()
        request = WebdriverRequest(self.root_url + xml_path, callback=self.parse_images)

        request.meta['item'] = item

        yield request

    def parse_images(self, response):
        sel = Selector(response)

        item = response.meta.get('item', ScraperProduct())
        l = ScraperProductLoader(item=item, response=response)

        urls = sel.css('image[url*="touchzoom"]::attr(url)').extract()
        image_urls = set(['{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1]) for url in urls])

        l.add_value('image_urls', image_urls)

        yield l.load_item()
