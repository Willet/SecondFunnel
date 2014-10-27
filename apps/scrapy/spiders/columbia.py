import re

from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.assets.models import Product


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
        is_product_page = sel.css('span[itemprop="productID"]') or sel.css('.error-page-message')
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

        # item is out of stock / removed
        if sel.css('.error-page-message'):
            prod = Product.objects.get(url=response.url)
            prod.in_stock = False
            prod.save()
            return

        sku = sel.css('span[itemprop="productID"]::text').extract()[0]

        colors = sel.css('ul.variationcolor li a::attr(href)').extract()
        colors = ['_' + re.findall('(?<=variationColor=)\d+', href)[0] + '_' for href in colors]
        print "{} colors".format(len(colors))


        for color in colors:
            print "color variant:", color
            l = ScraperProductLoader(item=ScraperProduct(), response=response)

            l.add_value('url', response.url.split('?')[0])
            l.add_css('name', '.product-name::text')
            l.add_css('description', 'div.product-summary::text')

            l.add_css('details', '.pdpDetailsContent div::text')

            attributes = {}
            if len(sel.css('div.product-price span')) > 1: # on sale
                l.add_css('price', 'span.price-standard::text')
                sale_price = sel.css('span.price-sales::text')[0].extract()
                attributes['sale_price'] = sale_price[sale_price.index('$'):].strip()
            else:
                l.add_css('price', 'span.reg-price::text')
                attributes['sale_price'] = ''

            categories = sel.css('ol.breadcrumb a::text').extract()[1:]  # Skip the first element

            attributes['categories'] = categories
            l.add_value('attributes', attributes)

            img_urls = sel.css('img.s7productthumbnail::attr(data-m-src)').extract()
            if len(img_urls) == 0:  # only 1 image means no thumbnails apparently
                img_urls = sel.css('#s7basiczoom_div::attr(data-defaultasset)').extract()

            l.add_value('sku', sku + '@' + color[1:-1])
            image_urls = []
            for img_url in img_urls:
                image_urls.append(re.sub('_\d{3}_', color, img_url, count=1))
            l.add_value('in_stock', bool(image_urls))
            l.add_value('image_urls', image_urls)
            yield l.load_item()
