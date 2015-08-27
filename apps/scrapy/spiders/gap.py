from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class GapSpider(SecondFunnelCrawlScraper):
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

        url_sel = sel.css('link[rel="canonical"]::attr(href)')
        their_id = url_sel.re("/P(\d+).jsp")[0]
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', url_sel.extract()[0])
        l.add_value('sku', their_id)
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

        try:
            category_name = sel.css('#lnc-division::attr(alt)').extract()[0]
        except IndexError:
            category_name = sel.css('ul.category li.category')[0].css('a::text').extract()[0]
        l.add_value('attributes', attributes)

        # image urls are stored in the "productData" page
        url = self.product_data_url.format(their_id)
        request = WebdriverRequest(url, callback=self.images)
        # request contains other data in meta['item']
        request.meta['item'] = l.load_item()
        yield request  # crawl the other url

    def images(self, response):
        sel = Selector(response)
        item = response.meta.get('item', ScraperProduct())
        l = ScraperProductLoader(item=item, response=response)

        relative_urls = sel.css("body").re(r"Z':\s?'([^']+?)'")
        image_urls = [self.root_url + x for x in relative_urls]

        l.add_value("image_urls", image_urls)

        yield l.load_item() # the actual item is yielded, now with images
