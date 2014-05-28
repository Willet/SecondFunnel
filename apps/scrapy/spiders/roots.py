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
        l.add_css('sku', 'link[rel="canonical"]::attr(href)', re='/P(\d+).jsp')
        l.add_css('name', '.productName::text')

        # Presence of product name determines product availability
        l.add_value('in_stock', bool(l.get_output_value('name')))

        # TODO: Sanitize output with bleach
        l.add_css('description', '#tabWindow')

        # TODO: Extract *all* images
        l.add_css('image_urls', '#product_image_bg img::attr(src)')

        attributes = {}
        sale_price = sel.css('#priceText .salePrice::text').extract_first()

        if not sale_price:
            l.add_css('price', '#priceText::text')
        else:
            l.add_css('price', '#priceText strike::text')
            attributes['sales_price'] = sale_price

        category_sel = sel.css('li a[class*=selected]')
        category_url = category_sel.css('::attr(href)').extract_first()
        category_name = category_sel.css('::text').extract_first()

        attributes['categories'] = []
        attributes['categories'].append((category_name, category_url))
        l.add_value('attributes', attributes)

        yield l.load_item()
