import re
import urlparse

from scrapy.selector import Selector
from scrapy.contrib.spiders import Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct

class AeropostaleSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'aeropostale'
    root_url = "http://www.aeropostale.com"
    allowed_domains = ['aeropostale.com']
    
    store_slug = name
    rules = [
        Rule(SgmlLinkExtractor(restrict_xpaths='//div[contains(@class, "details-image")]'), 
                           callback='parse_product', follow=False),
        Rule(SgmlLinkExtractor(restrict_xpaths='//li[contains(@class, "viewAll")]'))
    ]

    def __init__(self, *args, **kwargs):
    	super(AeropostaleSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        return sel.css('#productPage')

    def parse_product(self, response):
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        # attributes = response.meta.get('attributes', {})
        
        sku = urlparse.parse_qs(urlparse.urlparse(response.url).query)['productId'][0]

        l.add_css('name', '.right h2::text')
        l.add_css('price', '.price .now::text', re='(\d+)')
        l.add_value('sku', sku)
        l.add_css('details', '.product-description')
        l.add_css('url', 'link[rel="canonical"]::attr(href)')

        base_img = self.root_url + sel.css('img.zoom::attr(src)').extract()[0]
        colors = sel.css('ul.swatches.clearfix li img::attr(src)').re('-(\d+)_')
        img_urls = [re.sub('-\d+enh', '-'+color+'enh', base_img) for color in colors]
        l.add_value('image_urls', img_urls)

        attributes = {}
        
        # who needs one category when fifty eight thousand will do?
        categories = []

        genders = sel.css('#nav-categories a.aeroNavBut')
        if genders[0].css('.current'):
            categories.append('girls')
        elif genders[1].css('current'):
            categories.append('boys') 
 
        if float(l.get_output_value('price')) < 10:
            categories.append('under $10')
        elif float(l.get_output_value('price')) < 20:
            categories.append('under $20')

        gender = sel.css('.hasChildren.active a::text').extract()
        if gender:
            categories.append(gender[0])

        attributes['categories'] = categories

        l.add_value('attributes', attributes)

        yield l.load_item()
