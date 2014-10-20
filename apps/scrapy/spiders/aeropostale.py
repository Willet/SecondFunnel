import re
import urlparse
import time

from scrapy.selector import Selector
from scrapy.contrib.spiders import CrawlSpider
from scrapy.contrib.spiders import Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy_webdriver.http import WebdriverRequest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct

class AeropostaleSpider(SecondFunnelCrawlScraper, CrawlSpider):
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
        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        
        sku = urlparse.parse_qs(urlparse.urlparse(response.url).query)['productId'][0]

        l.add_css('name', '.right h2::text')
        l.add_css('price', '.price .now::text', re='(\d+)')
        l.add_value('sku', sku)
        a = sel.css('.product-description').extract()[0].replace("<br>", "</p><p>")
        l.add_value('description', a)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')

        base_imgs = sel.css('#altimages img::attr(src)').extract()
        if not base_imgs:
            base_imgs = sel.css('#mainProductImage::attr(src)').extract()
        base_imgs = [re.sub(r't\d+x\d+\.jpg', 'enh-z5.jpg', img) for img in base_imgs]

        colors = sel.css('ul.swatches.clearfix li img::attr(src)').re('-(\d+)_')
        image_urls = []
        for color in colors:
            for base_img in base_imgs:
                image_urls.append(self.root_url + re.sub('-\d+enh', '-'+color+'enh', base_img))
        l.add_value('image_urls', image_urls)

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
