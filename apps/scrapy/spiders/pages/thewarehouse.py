import json

from scrapy.linkextractors.sgml import SgmlLinkExtractor
from scrapy.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class TheWarehouseSpider(SecondFunnelCrawlSpider):
    name = 'thewarehouse'
    store_slug = name
    allowed_domains = ['thewarehouse.co.nz']
    root_url = 'http://www.thewarehouse.co.nz'
    visited = []
    rules = []

    def __init__(self, *args, **kwargs):
        super(TheWarehouseSpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        """
        Assume url is datafeed
        """
        if self.is_product_feed(response):
            return parse_feed(response)
        else:
            self.log("Not a feed page: {}".format(response.url))
            return []

    def is_product_feed(self, response):
        return bool('json' in response.url.lower())
    
    def parse_feed(self, response):
        """
        Parses a json datafeed page on The Warehouse

        Designed for: http://www.thewarehouse.co.nz/red/catalog/gifting/gifts-for-him?JsonFlag=true
        """
        jsonresponse = json.loads(response.body_as_unicode())

        for product in jsonresponse['products']:
            l = ScraperProductLoader(item=ScraperProduct(), response=response)
            l.add_value('url', product['productUrl'])
            l.add_value('sku', product['productSku'])
            l.add_value('name', product['productName'])
            l.add_value('in_stock', product['derivedInStock'])
            l.add_value('description', product['productDescription'])
            l.add_value('price', product['price'])
            l.add_value("image_urls", [product['productImageUrl']])
            l.add_value("price", product['price'])

            if len(product['productPriceInfo']):
                l.add_value('attributes', product['productPriceInfo'])

            yield l.load_item()

        # If the feed continues on another page, follow it
        if jsonresponse.get('nextPageUrl'):
            yield WebdriverRequest(jsonresponse.get('nextPageUrl'), callback=self.parse_feed)
