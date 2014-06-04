from urlparse import urljoin
from scrapy import log
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, SecondFunnelScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class GapSpider(SecondFunnelScraper, WebdriverCrawlSpider):
    name = 'gap'
    allowed_domains = ['gap.com']
    start_urls = ['http://www.gap.com/']
    rules = [
        # Rule(SgmlLinkExtractor(allow=[
        #     r'\/browse\/subDivision.do\?.*?cid=\d+'
        # ]), 'parse_division'),
        # Rule(SgmlLinkExtractor(allow=[
        #     r'\/browse\/category.do\?.*?cid=\d+'
        # ]), 'parse_category'),
        Rule(SgmlLinkExtractor(allow=[
            r'/browse/product.do\?.*?pid=\d+'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name

    # TODO: Handle 'styles'
    category_url = 'http://www.gap.com/browse/category.do?cid={}'
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

        if response.url in self.visited:
            return []

        sel = Selector(response)
        pages = sel.css('.pagePaginatorLabel').re_first('Page \d+ of (\d+)')

        if not pages or int(pages) <= 1:
            return []

        urls = []
        pages = int(pages)
        for page in xrange(pages):
            url = '{base}#pageId={page}'.format(base=response.url, page=page)
            self.visited.append(url)
            urls.append(WebdriverRequest(url))

        return urls

    def parse_division(self, response):
        sel = Selector(response)
        base_url = response.url

        divisions = sel.css('.category > a')

        for division in divisions:
            url = division.css('::attr(href)').extract_first().strip()
            text = division.css('::text').extract_first().strip()
            msg = u'PARSE_DIVISION - {category}: {url}'.format(url=url,
                                                               category=text)
            log.msg(msg, level=log.DEBUG)

            yield WebdriverRequest(urljoin(base_url, url))

    def parse_category(self, response):
        sel = Selector(response)
        base_url = response.url

        products = sel.css('.productCatItem > a')

        for product in products:
            url = product.css('::attr(href)').extract_first().strip()
            text = product.css('::text').extract_first().strip()
            msg = u'PARSE CATEGORY - {product}: {url}'.format(url=url,
                                                              product=text)
            log.msg(msg, level=log.DEBUG)

            yield WebdriverRequest(urljoin(base_url, url))

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
