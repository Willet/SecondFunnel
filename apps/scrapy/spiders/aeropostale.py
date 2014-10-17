import re
import urlparse
import time

from scrapy.selector import Selector
from scrapy.contrib.spiders import Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy_webdriver.http import WebdriverRequest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

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
        Rule(SgmlLinkExtractor(restrict_xpaths='//li[contains(@class, "viewAll")]/a[contains(text(), "100")]'))
    ]

    def __init__(self, *args, **kwargs):
    	super(AeropostaleSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        return sel.css('#productPage')

    def parse_product(self, response):
        response.request.manager.webdriver.implicitly_wait(10)

        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        # attributes = response.meta.get('attributes', {})
        
        sku = urlparse.parse_qs(urlparse.urlparse(response.url).query)['productId'][0]

        l.add_css('name', '.right h2::text')
        l.add_css('price', '.price .now::text', re='(\d+)')
        l.add_value('sku', sku)
        l.add_css('description', '.product-description')
        l.add_css('url', 'link[rel="canonical"]::attr(href)')

        # # try once
        # try:
        base_img = self.root_url + sel.css('img.zoom::attr(src)').extract()[0]
        # except IndexError:
        #     # try one more time
        #     try:
        #         base_img = re.findall(r'background-image:\s*url\(([^)]+)\)', sel.css('#zoomIn::attr(style)').extract()[0])[0]
        #         base_img = re.sub(r't\d+x\d+\.jpg', 'enh-z5.jpg', base_img)
        #     except IndexError as e:
        #         # give up
        #         print "This page is fucking slow / has way too much javascript.  Images did not load.  \
        #                We will try this page again at the end."
        #         print "cause:", e
        #         print "url:", response.url
        #         yield WebdriverRequest(response.url, callback=self.parse_product)
        #         return


        colors = sel.css('ul.swatches.clearfix li img::attr(src)').re('-(\d+)_')
        img_urls = [re.sub('-\d+enh', '-'+color+'enh', base_img) for color in colors]
        l.add_value('image_urls', img_urls)

        attributes = {}
        
        # who needs one category when fifty eight thousand will do?
        categories = []

        genders = sel.css('#nav-categories a.aeroNavBut')
        if genders[0].css('.current'):
            categories.append('girls')
        elif genders[1].css('.current'):
            categories.append('guys')
 
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
