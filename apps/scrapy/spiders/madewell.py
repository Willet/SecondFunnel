from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import SecondFunnelScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class MadewellSpider(SecondFunnelScraper, WebdriverCrawlSpider):
    name = 'madewell'
    allowed_domains = ['madewell.com']
    start_urls = ['http://www.madewell.com/']
    rules = [
        Rule(SgmlLinkExtractor(allow=[
            r'/\w+\d+.jsp'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name
    product_url = 'http://www.madewell.com/madewell_category/PRDOVR~{0}/{0}.jsp'

    def __init__(self, *args, **kwargs):
        if kwargs.get('products'):
            # Mostly used for multi-product scraping
            # For example, this URL:
            #
            #    https://www.madewell.com/browse/multi_product_detail.jsp?externalProductCodes=00000%3AA2330%3AA0379%3AA6319%3AA7928%3AA1718%3AA6306%3AA6308%3A03957%3AA2006%3AA6310%3AA6347&FOLDER%3C%3Efolder_id=2534374302027304&bmUID=kk2rB9Q
            #
            # ... is really this URL ...
            #
            #   https://www.madewell.com/browse/multi_product_detail.jsp?externalProductCodes=00000:A2330:A0379:A6319:A7928:A1718:A6306:A6308:03957:A2006:A6310:A6347&FOLDER<>folder_id=2534374302027304&bmUID=kk2rB9Q
            #
            # ... which is really just these products:
            #
            #   00000:A2330:A0379:A6319:A7928:A1718:A6306:A6308:03957:A2006:A6310:A6347
            #
            # Except for 00000 (which is invalid)

            self.products = kwargs.get('products').split(',')
            self.start_urls = [
                self.product_url.format(c) for c in self.products
            ]

        super(MadewellSpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        if self.is_product_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_product(response)

        return []

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.item-num')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on Madewell.com.

        @url https://www.madewell.com/madewell_category/DENIM/boyjean/PRDOVR~A5477/A5477.jsp
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls
        """
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', '.item-num::text', re='item (\w+\d+)')
        l.add_css('name', 'h1::text')
        l.add_css('price', '.full-price span::text', re='USD (.*)')
        l.add_value('in_stock', True)

        l.add_css('description', '#prodDtlBody')
        l.add_css('image_urls', '.float-left img::attr(data-imgurl)')

        # Madewell categories are tricky

        yield l.load_item()
