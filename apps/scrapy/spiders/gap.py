from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class GapSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'gap'
    allowed_domains = ['gap.com']
    start_urls = ['http://www.gap.com/']
    rules = [
        Rule(SgmlLinkExtractor(allow=[
            r'/browse/product.do\?.*?pid=\d+'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name

    root_url = 'http://www.gap.com'
    category_url = 'http://www.gap.com/browse/category.do?cid={}'
    product_data_url = 'http://www.gap.com/browse/productData.do?pid={}'
    visited = []

    def __init__(self, *args, **kwargs):
        if kwargs.get('categories'):
            self.categories = kwargs.get('categories').split(',')
            self.start_urls = [
                self.category_url.format(c) for c in self.categories
            ]

        super(GapSpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        """
        Handles any special parsing from start_urls.

        However, we mostly use it to handle pagination.

        This method is misleading as it actually cascades...
        """
        if self.is_product_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_product(response)

        if response.url in self.visited:
            return []

        sel = Selector(response)
        pages = sel.css('.pagePaginatorLabel').re_first(r'Page \d+ of (\d+)')

        if not pages or int(pages) <= 1:
            return []

        urls = []
        pages = int(pages)
        for page in xrange(pages):
            url = '{base}#pageId={page}'.format(base=response.url, page=page)
            self.visited.append(url)
            urls.append(WebdriverRequest(url))

        return urls

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('link[rel="canonical"]::attr(href)')\
            .re_first(r'/P(\d+).jsp')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on Gap.com.

        @url http://www.gap.com/browse/product.do?cid=64526&vid=1&pid=960079012
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', response.url)
        l.add_css('sku', 'link[rel="canonical"]::attr(href)', re=r'/P(\d+).jsp')
        l.add_css('name', '.productName::text')

        # Presence of product name determines product availability
        l.add_value('in_stock', bool(l.get_output_value('name')))

        l.add_css('description', '#tabWindow')

        attributes = {}
        sale_price = sel.css('#priceText .salePrice::text').extract_first()

        if not sale_price:
            l.add_css('price', '#priceText::text')
        else:
            l.add_css('price', '#priceText strike::text')
            attributes['sales_price'] = sale_price

        category_name = sel.css('#lnc-division::attr(alt)').extract()[0]

        attributes['categories'] = [category_name]
        l.add_value('attributes', attributes)

        img_urls = sel.css('#imageThumbs input::attr(src)').extract()
        big_urls = []
        for url in img_urls:
            bits = url.split('/')
            # MAJIC
            # basically something like: http://www.gap.com/webcontent/0008/097/815/cn8097815.jpg
            # needs to become like:     http://www.gap.com/webcontent/0008/097/812/cn8097812.jpg
            bits[-2] = str(int(bits[-2]) - 3) # 3 is my favourite number
            more_bits = bits[-1].split('.')
            more_bits[0] = more_bits[0][:-3] + bits[-2]
            bits[-1] = '.'.join(more_bits)
            big_urls.append('/'.join(bits))
        l.add_value('image_urls', big_urls)

        yield l.load_item()

