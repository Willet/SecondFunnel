from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from urlparse import urlparse
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class DotAndBoSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'dotandbo'
    allowed_domains = ['dotandbo.com']
    remove_background = False
    start_urls = ['http://www.dotandbo.com/']
    rules = [
        # dot and bo does not paginate collections.
        # to add a handler that handles pagination (next) links,
        # refer to other scrapers.
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//div[@id="wrapper"]//h2/a'),
            'parse_product', follow=False
        )
    ]

    store_slug = name

    def __init__(self, *args, **kwargs):
        super(DotAndBoSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.order-box')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on DotAndBo.com.

        @url http://www.dotandbo.com/collections/best-sellers/book-escape-wall-shelves
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', 'span.sku::text')
        l.add_css('name', '#wrapper section.product-block h1::text')
        l.add_css('price', '.item_msrp::text')

        # <span class="item_percentoff">43</span>

        # TODO: actually GAF and calculate if the thing is on sale
        # <meta property="dotandbo:sale_ends" content="2014-02-16T03:00:00-08:00"/>
        l.add_value('in_stock', True)

        l.add_css('description', '#tab1 > p')

        # http://d10125bvdzznt0.cloudfront.net/products/26098/square2wide/DIM0119-1.jpg ->
        # http://d10125bvdzznt0.cloudfront.net/products/26098/original/DIM0119-1.jpg
        image_urls = sel.css('#wrapper div.gallery-thumbnails '
                             'img::attr(src)').extract()
        image_urls = [u.replace('square2wide', 'original') for u in image_urls]
        l.add_value('image_urls', image_urls)

        # Handle categories
        breadcrumb = sel.css('.breadcrumb a')[-1]
        category_name = breadcrumb.css('::text').extract_first().strip()
        category_url = breadcrumb.css('::attr(href)').extract_first()

        attributes = {}
        attributes['categories'] = [(category_name, category_url)]
        l.add_value('attributes', attributes)

        sale_price = '$' + sel.css('meta[property="og:price:amount"]::attr("content")').extract_first()
        percent_off = sel.css(".item_percentoff::text").extract_first()
        if l.load_item()['price'] != sale_price:
            attributes['sale_price'] = sale_price
            attributes['percent_off'] = percent_off

        yield l.load_item()
