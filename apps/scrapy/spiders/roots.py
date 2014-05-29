from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider
from apps.scrapy.utils import open_in_browser, ScraperProductLoader


class RootsSpider(WebdriverCrawlSpider):
    name = 'roots'
    allowed_domains = ['usa.roots.com', 'canada.roots.com']
    start_urls = ['http://usa.roots.com/women/best-sellers/womensBestSellers,default,sc.html']
    rules = [
        Rule(SgmlLinkExtractor(allow=[r'pd.html']),
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
        l.add_css('sku', '#productdetails .key::text', re='(\d+)')
        l.add_css('name', '#productName::text')

        # TODO: Sanitize output with bleach
        l.add_css('description', '.prodctdesc .description::text')

        # TODO: WTF does this need to be this complicated?
        image_urls = [x.css('::attr(src)').extract_first()
                      for x in
                      sel.xpath('//div[contains(@class, "fluid-display-imagegroup")]//img[contains(@class, ":view")]')]

        attributes = {}
        sale_price = sel.css('.pricing #priceTop .special .value::text').extract_first()

        if not sale_price:
            l.add_css('price', '.pricing #priceTop .value::text')
        else:
            l.add_css('price', '.pricing #priceTop .standard .value::text')
            attributes['sales_price'] = sale_price

        attributes['categories'] = []
        category_sels = sel.css('.breadcrumbs').xpath('a[@href!="#"]')
        for category_sel in category_sels:
            category_url = category_sel.css('::attr(href)').extract_first()
            category_name = category_sel.css('::text').extract_first().strip()
            attributes['categories'].append((category_name, category_url))

        l.add_value('image_urls', image_urls)
        l.add_value('attributes', attributes)

        yield l.load_item()
