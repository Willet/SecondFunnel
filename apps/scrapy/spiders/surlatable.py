import re
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from urlparse import urlparse
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider,\
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.utils.misc import open_in_browser


class SurlatableSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'surlatable'
    allowed_domains = ['surlatable.com']
    start_urls = []
    rules = [
        Rule(SgmlLinkExtractor(allow=[r'.*product/PRO-.*']),
             callback='parse_product',
             follow=False)
    ]

    store_slug = name
    visited = []

    def __init__(self, *args, **kwargs):
        return super(SurlatableSpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        """
        Handles any special parsing from start_urls.

        However, we mostly use it to handle pagination.

        This method is misleading as it actually cascades...
        """
        # scrape individual products.
        if self.is_product_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_product(response)

        if response.url in self.visited:
            return []

        sel = Selector(response)
        pages = sel.xpath('//*[@class="pagination"][1]')\
            .css('.pageno::attr(href)').extract()

        meta = {}
        category_url, category_name = (response.url,
            sel.css('#main #sidebar h1::text').extract_first())
        if category_name:
            meta = {category_name: category_url}

        if not pages:
            return []

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        page_iter = iter(pages)
        page = next(page_iter)  # Skip first page, as usual

        urls = []
        for page in page_iter:
            page_url = hostname + page
            self.visited.append(page_url)
            request = WebdriverRequest(page_url)
            request.meta['categories'] = meta
            urls.append(request)

        return urls

    def is_product_page(self, response):
        is_product_page = re.search('.*product/PRO-.*', response.url)
        return bool(is_product_page)

    def parse_product(self, response):
        """
        Parses a product page on SurLaTable.com.

        @url http://www.surlatable.com/product/PRO-1447598/Fish+Individual+Bowl
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price description image_urls attributes
        """

        url = response.url
        referer = response.request.headers.get('Referer')

        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', response.url)
        l.add_css('name', 'h1.name::text')
        l.add_css('description', '#description span.boxsides')
        l.add_value("sku", response.url, re='(\d+)')

        attributes = {}

        sale_price = sel.css('li.sale::text').re_first('(\$\d+\.\d+)')

        if sale_price:
            attributes['sale_price'] = sale_price
            l.add_css('price', 'li.regular::text', re='(\$\d+\.\d+)')
        else:
            l.add_css('price', 'li.price::text', re='(\$\d+\.\d+)')

        if referer:
            attributes['categories'] = {
                'name': referer,
            }

        l.add_value('attributes', attributes)

        # URL
        magic_values = sel.css('.fluid-display::attr(id)')\
            .extract_first()\
            .split(':')
        xml_path = '/images/customers/c{1}/{2}/' \
            '{2}_{3}/pview_{2}_{3}.xml'.format(*magic_values)

        item = l.load_item()
        request = WebdriverRequest(
            hostname + xml_path, callback=self.parse_images)

        request.meta['item'] = item

        yield request

    def parse_images(self, response):
        sel = Selector(response)

        item = response.meta.get('item', ScraperProduct())
        l = ScraperProductLoader(item=item, response=response)

        xml_url = response.url
        path = xml_url.rsplit('/', 1)[0]

        # There may be cleaner ways to do this but they don't have THIS HAT.
        relative_urls = sel.xpath('//*[@id="TOUCHZOOM"]/../@url').extract()
        image_urls = [
            '{0}/{1}'.format(path, u.rsplit('/', 1)[1]) \
            for u in relative_urls
        ]

        l.add_value('image_urls', image_urls)

        yield l.load_item()
