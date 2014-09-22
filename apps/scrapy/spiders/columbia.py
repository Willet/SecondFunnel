from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader
import re


class ColumbiaSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'columbia'
    allowed_domains = ['columbia.com']
    start_urls = ['http://www.columbia.com/']
    start_urls_separator = '|'
    rules = [
        Rule(SgmlLinkExtractor(restrict_xpaths=['//div[contains(@class, "product-image")]']), callback='parse_product', follow=False)
    ]

    store_slug = name

    def __init__(self, *args, **kwargs):
        super(ColumbiaSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('span[itemprop="productID"]')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on Columbia.com.

        @url http://www.columbia.com/Men%27s-Royce-Peak%E2%84%A2-Zero-Short-Sleeve-Shirt/AM9112,default,pd.html
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description details image_urls attributes
        """

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', response.url.split('?')[0])
        l.add_css('sku', 'span[itemprop="productID"]::text')
        l.add_css('name', '.product-name::text')
        l.add_value('in_stock', True)

        l.add_css('description', 'div.product-summary::text')

        l.add_css('details', '.pdpDetailsContent div::text')

        img_urls = sel.css('img.s7productthumbnail::attr(data-m-src)').extract()
        # Hack
        # get same product imgs with all the different colors
        colors = ['_' + href.split('=')[-1] + '_' for href in sel.css('ul.variationcolor li a::attr(href)').extract()]
        colored_img_urls = []
        for img_url in img_urls:
            for color in colors:
                colored_img_urls.append(re.sub('_\d{3}_', color, img_url, count=1))
        l.add_value('image_urls', colored_img_urls)

        attributes = {}
        if len(sel.css('div.product-price span')) > 1: # on sale
            l.add_css('price', 'span.price-standard::text')
            sale_price = sel.css('span.price-sales::text')[0].extract()
            attributes['sale_price'] = sale_price[sale_price.index('$'):].strip()
        else:
            l.add_css('price', 'span.reg-price::text')

        # Handle categories
        breadcrumbs = sel.css('ol.breadcrumb a')[1:] # Skip the first element

        categories = []
        for breadcrumb in breadcrumbs:
            category_name = breadcrumb.css('::text').extract_first().strip()
            category_url = breadcrumb.css('::attr(href)').extract_first()

            categories.append((category_name, category_url))

        attributes['categories'] = categories
        l.add_value('attributes', attributes)

        yield l.load_item()
