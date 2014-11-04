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
from apps.assets.models import Product

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

        return sel.css('#productPage') or "noResults" in response.url

    def parse_product(self, response):
        sel = Selector(response)
        qs = urlparse.parse_qs(urlparse.urlparse(response.url).query)
        try:
            sku = qs['productId'][0]
        except KeyError:
            sku = qs['kw'][0]

        if "noResults" in response.url:
            product = Product.objects.get(sku=sku)
            product.in_stock = False
            product.save()
            return

        colors = sel.css('ul.swatches.clearfix li img::attr(src)').re('-(\d+)_')
        print "{} colors".format(len(colors))

        for color in colors:
            l = ScraperProductLoader(item=ScraperProduct(), response=response)

            l.add_css('name', '.right h2::text')
            l.add_css('price', '.price .now::text', re='(\d+)')
            l.add_value('sku', sku + "@" + color)
            a = sel.css('.product-description').extract()[0].replace("<br>", "</p><p>")
            l.add_value('description', a)
            l.add_css('url', 'link[rel="canonical"]::attr(href)')

            base_imgs = sel.css('#altimages img::attr(src)').extract()
            if not base_imgs:
                base_imgs = sel.css('#mainProductImage::attr(src)').extract()
            base_imgs = [re.sub(r't\d+x\d+\.jpg', 'enh-z5.jpg', img) for img in base_imgs]

            image_urls = []
            for base_img in base_imgs:
                image_urls.append(self.root_url + re.sub(r'-\d+(?=(_alternate\d+_)?enh)', '-'+color, base_img))
            l.add_value('image_urls', image_urls)

            attributes = {}

            # who needs one category when fifty eight thousand will do?
            categories = []
            categories += sel.css('#breadcrumbs a::text').extract()[1:-1]
            categories += sel.css('#sidebar-left .active a::text').extract()

            size_charts = sel.css('#sidebar-left dl dd dl dt a::text').extract()[-1]
            categories += re.findall(r'Aero ([^\s]*) Size Chart', size_charts)

            if float(l.get_output_value('price')) < 10:
                categories.append('under $10')
            elif float(l.get_output_value('price')) < 20:
                categories.append('under $20')


            attributes['categories'] = categories

            l.add_value('attributes', attributes)

            yield l.load_item()
