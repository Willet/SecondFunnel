from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider


class RootsSpider(WebdriverCrawlSpider):
    name = 'roots'
    allowed_domains = ['usa.roots.com', 'canada.roots.com']
    start_urls = ['http://usa.roots.com/']
    rules = [
        Rule(SgmlLinkExtractor(allow=[r'pd.html']),
             callback='parse_product',
             follow=False)
    ]

    store_slug = name

    # TODO: Handle 'styles'
    category_url = 'http://www.roots.com/browse/category.do?cid={}'

    def __init__(self, *args, **kwargs):
        super(RootsSpider, self).__init__()

        if kwargs.get('categories'):
            categories = kwargs.get('categories').split(',')
            self.start_urls = [self.category_url.format(c) for c in categories]

    # For some reason, Always defaults to regular requests...
    # So, we override...
    def start_requests(self):
        return [WebdriverRequest(url) for url in self.start_urls]

    def parse_product(self, response):
        sel = Selector(response)

        item = ScraperProduct()
        item['attributes'] = {}
        item['image_urls'] = []
        item['store'] = self.name

        url = response.url
        item['url'] = url

        sku = sel.css('link[rel="canonical"]::attr(href)').\
            re_first('/P(\d+).jsp')
        if sku:
            item['sku'] = sku

        product_name = sel.css('.productName::text')\
            .extract_first()

        # Presence of product name determines product availability
        if product_name:
            item['name'] = product_name
            item['in_stock'] = True
        else:
            item['in_stock'] = False

        description = sel.css('#tabWindow').extract_first()
        if description:
            item['description'] = description

        sale_price = sel.css('#priceText .salePrice::text').extract_first()

        if not sale_price:
            price = sel.css('#priceText::text').extract_first()
        else:
            price = sel.css('#priceText strike::text').extract_first()
            item['attributes']['sales_price'] = sale_price

        if price:
            item['price'] = price

        category_sel = sel.css('li a[class*=selected]')
        category_url = category_sel.css('::attr(href)').extract_first()
        category_name = category_sel.css('::text').extract_first()

        item['attributes']['categories'] = []
        item['attributes']['categories'].append((category_name, category_url))

        # Mostly for proof of concept
        image = sel.css('#product_image_bg img::attr(src)').extract_first()
        if image:
            item['image_urls'].append(image)

        yield item
