from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper, WebdriverCrawlSpider
from scrapy.selector import Selector
from scrapy.contrib.spiders import Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct



class CrocsSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'crocs'
    allowed_domains = ["crocs.com"]
    start_urls = ['http://www.crocs.com/']
    rules = [
        Rule (
            SgmlLinkExtractor(restrict_xpaths='//a/img[contains(@alt, "Go to Next Page")]/..')
        ),
        Rule (
            SgmlLinkExtractor(restrict_xpaths='//div[contains(@class, "productThumb")]'),
            callback='parse_product', follow=False
        )
    ]
    store_slug = name

    def __init__(self, *args, **kwargs):
        super(CrocsSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)
        return sel.css("#pdpHeaderPrice")

    def parse_product(self, response):
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('name', 'h1#pname::text')
        l.add_css('description', 'h3 a::text')
        l.add_css('details', '.productDetailsCopy')
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('sku', '.itemNum::text')

        l.add_css('image_urls', '#productHeroImg::attr(data-zoom-image)')

        attributes = {}

        breadcrumbs = sel.css('#crumbs a::text').extract()
        attributes['categories'] = breadcrumbs[1:] # first crumb is the "back" button, so ignore it

        sel_price = sel.css('h3.price')
        if sel_price.css('span'):
            l.add_css('price', 'span[style*="line-through"]::text')
            price = sel_price.css('span.saleRedText::text').extract()[0]
            attributes['sale_price'] = price[price.index('$'):]
        else:
            l.add_css('price', 'h3.price::text')


        l.add_value('attributes', attributes)

        yield l.load_item()

