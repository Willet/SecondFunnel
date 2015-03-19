from scrapy import log
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

    remove_background = False

    rules = [
        Rule(SgmlLinkExtractor(allow=[
            r'/product/PRO-\d+(/.*)?'
        ]), 'parse_recipe', follow=False),
        Rule(SgmlLinkExtractor(allow=[
            r'/product/REC-\d+(/.*)?'
        ]), 'parse_recipe', follow=False),
        # Old way, may cover more cases?
        #Rule(SgmlLinkExtractor(restrict_xpaths=
        #    "//div[contains(@id, 'items')]/div[contains(@class, 'row')]/dl[contains(@class, 'item')]"
        #), callback="parse_product", follow=False),
    ]

    def __init__(self, *args, **kwargs):
        super(SurLaTableSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)
        return sel.css('#productdetail label#productPriceValue')

    def is_sold_out(self, response):
        return False
        
    def parse_product(self, response):
        if not self.is_product_page(response):
            return

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        attributes = {}

        l.add_value('in_stock', True)
        l.add_css('name', 'h1.name::text')
        l.add_css('sku', '#productId::attr(value)', re=r'\d+')
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('description', '#description .boxsides')

        # prices are sometimes in the forms:
        #    $9.95 - $48.96
        #    Now: $99.96 Was: $139.95 Value: $200.00
        price_range = sel.css('meta[property="eb:pricerange"]::attr(content)').extract()[0]
        if price_range:
            attributes['price_range'] = price_range
        try:
            reg_price = sel.css('.regular label#productPriceValue::text').extract()[0].split('-')[0]
        except IndexError:
            reg_price = sel.css('.price label#productPriceValue::text').extract()[0].split('-')[0]
        else:
            sale_price = sel.css('.sale label#productPriceValue::text').extract()[0].split('-')[0]
            l.add_value('sale_price', sale_price)
        
        l.add_value('price', reg_price)
        l.add_value('attributes', attributes)
        item = l.load_item()

        magic_values = sel.css('.fluid-display::attr(id)').extract_first().split(':')
        xml_path = '/images/customers/c{1}/{2}/{2}_{3}/pview_{2}_{3}.xml'.format(*magic_values)
        request = WebdriverRequest(self.root_url + xml_path, callback=self.parse_images)

        request.meta['item'] = item

        yield request

    def parse_recipe(self, response):
        #sel = Selector(response)
        log.msg('scraping recipe!')

    def parse_images(self, response):
        sel = Selector(response)

        item = response.meta.get('item', ScraperProduct())
        l = ScraperProductLoader(item=item, response=response)

        urls = sel.css('image[url*="touchzoom"]::attr(url)').extract()
        image_urls = set(['{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1]) for url in urls])

        # For Sur La Table, a product image doubles as a cover image. Choose first image & manually update later
        url = urls[0]
        item['attributes']['url'] = '{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1])
        
        l.add_value('image_urls', image_urls)

        yield l.load_item()
