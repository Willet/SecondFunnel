import json
import operator
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from urlparse import urlparse
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class RootsSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'roots'
    allowed_domains = ['usa.roots.com', 'canada.roots.com']
    start_urls = ['http://usa.roots.com/women/best-sellers/womensBestSellers,default,sc.html']
    start_urls_separator = "|"  # because urls above contain commas,
                                # now you need to separate urls in the terminal
                                # using this symbol.
    rules = [
        Rule(SgmlLinkExtractor(allow=[r'pd.html']),
             callback='parse_product',
             follow=False)
    ]

    store_slug = name

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('#productdetails .key')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on Roots.com.

        @url http://canada.roots.com/SmallBanffBagHorween/LeatherLuggageBags//18040023,default,pd.html?cgid=leatherWeekenderBags&selectedColor=Z65
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price description image_urls attributes
        """

        url = response.url
        # hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', response.url)
        l.add_css('sku', '#productdetails .key::text', re=r'(\d+)')
        l.add_css('name', '#productName::text')
        l.add_css('description', '.prodctdesc .description::text')

        attributes = {}
        sale_price = sel.css('.pricing #priceTop .special .value::text').extract_first()

        if not sale_price:
            l.add_css('price', '.pricing #priceTop .value::text')
        else:
            l.add_css('price', '.pricing #priceTop .standard .value::text')
            attributes['sale_price'] = sale_price

        attributes['categories'] = []
        category_sels = sel.css('.breadcrumbs').xpath('a[@href!="#"]')
        for category_sel in category_sels:
            category_url = category_sel.css('::attr(href)').extract_first()
            category_name = category_sel.css('::text').extract_first().strip()
            attributes['categories'].append((category_name, category_url))

        l.add_value('attributes', attributes)

        # URL
        root_path = 'http://demandware.edgesuite.net/aacg_prd/on/' \
                    'demandware.static/Sites-RootsCA-Site/' \
                    'Sites-roots_master_catalog/default/' \
                    'v1402349332188/customers'

        magic_values = sel.css('.fluid-display::attr(id)')\
            .extract_first()\
            .split(':')

        js_path = '/c{1}/{2}/{2}_{3}/js/data.js'.format(*magic_values)

        item = l.load_item()
        request = WebdriverRequest(root_path + js_path,
                                   callback=self.parse_images)

        request.meta['item'] = item

        yield request

    def parse_images(self, response):
        sel = Selector(response)

        item = response.meta.get('item', ScraperProduct())
        l = ScraperProductLoader(item=item, response=response)

        jsonp = sel.css('pre::text')\
            .re_first('product_view:({.*}),custom_template')
        data = json.loads(jsonp)

        xml_url = response.url
        path = xml_url.rsplit('/', 2)[0]

        # There may be cleaner ways to do this but they don't have THIS HAT.
        # This one is a doozy
        image_data = data.get('product_view', {}).get('image', [])
        relative_urls = (
            x.get('url')
            for x in image_data
            if 'TOUCHZOOM' in map(
                operator.itemgetter('id'), x.get('category_mapping')
            )
        )

        image_urls = [
            '{0}/{1}'.format(path, u.rsplit('/', 1)[1])
            for u in relative_urls
        ]

        l.add_value('image_urls', image_urls)

        yield l.load_item()
