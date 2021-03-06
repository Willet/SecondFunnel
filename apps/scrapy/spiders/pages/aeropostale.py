import re
import urlparse
import time

from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_webdriver.http import WebdriverRequest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct
from apps.assets.models import Product

class AeropostaleSpider(SecondFunnelCrawlSpider):
    name = 'aeropostale'
    root_url = "http://www.aeropostale.com"
    allowed_domains = ['aeropostale.com']
    
    store_slug = name
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//div[contains(@class, "details-image")]'), 
                           callback='parse_product', follow=False),
        Rule(LinkExtractor(restrict_xpaths='//div[contains(@class, "childProduct")]//h2'),
                           callback='parse_product', follow=False),
        Rule(LinkExtractor(restrict_xpaths='//area[contains(@title, "Shop the Look")]')),
        Rule(LinkExtractor(restrict_xpaths='//li[contains(@class, "viewAll")]/a[contains(text(), "100")]'))
    ]

    def __init__(self, *args, **kwargs):
    	super(AeropostaleSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        return sel.css('#productPage') or "noResults" in response.url


    def is_sold_out(self, response):
        return "noResults" in response.url


    def parse_product(self, response):
        sel = Selector(response)
        qs = urlparse.parse_qs(urlparse.urlparse(response.url).query)
        try:
            sku = qs['productId'][0]
        except KeyError:
            sku = qs['kw'][0]

        colors = sel.css('ul.swatches.clearfix li img::attr(src)').re(r'-(\d+)_')
        print "{} colors".format(len(colors))

        for color in colors:
            l = ScraperProductLoader(item=ScraperProduct(), response=response)
            attributes = {}

            l.add_css('name', '.right h2::text')
            l.add_value('sku', sku + "@" + color)
            a = sel.css('.product-description').extract()[0].replace("<br>", "</p><p>")
            l.add_value('description', a)
            l.add_css('url', 'link[rel="canonical"]::attr(href)')
            try:
                l.add_value('price', sel.css('.right .price li:not(.now)::text').re(r'([\d.]+)')[0])
                attributes['sale_price'] = '$' + sel.css('.right .price .now::text').re(r'([\d.]+)')[0]
            except:
                l.add_css('price', '.right .price li.now::text', re=r'([\d.]+)')
                attributes['sale_price'] = ''

            base_imgs = sel.css('#altimages img::attr(src)').extract()
            if not base_imgs:
                base_imgs = sel.css('#mainProductImage::attr(src)').extract()
            base_imgs = [re.sub(r't\d+x\d+\.jpg', 'enh-z5.jpg', img) for img in base_imgs]

            image_urls = []
            for base_img in base_imgs:
                image_urls.append(self.root_url + re.sub(r'-\d+(?=(_alternate\d+_)?enh)', '-'+color, base_img))
            l.add_value('image_urls', image_urls)

            l.add_value('attributes', attributes)

            yield l.load_item()
