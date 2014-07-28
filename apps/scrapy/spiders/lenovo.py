import re
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from urlparse import urlparse
import time
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.utils.misc import open_in_browser


class LenovoSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'lenovo'
    allowed_domains = ['lenovo.com', 'shop.lenovo.com']
    start_urls = ['http://shop.lenovo.com/us/en/tablets/']
    rules = [
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "next")]')
        ),
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "button") and contains(@class, "shop") and contains(@class, "full")]'),
            'parse_product', follow=False
        )
    ]

    store_slug = 'lenovo'

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('.product-style')

        return is_product_page


    def parse_product(self, response):
        """
        Parses a product page on Lenovo.com.

        @url http://shop.lenovo.com/us/en/tablets/lenovo/yoga-tablet-series/
        @returns items 1 10
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        skus = (sel.css('meta[name="SKU"]::attr(content)').extract_first().split(','))
        first_sku = skus[0]
        l.add_value('sku', first_sku)

        product_name = u"{} {} {}".format(
            sel.css('meta[name="ProductName"]::attr(content)').extract_first(),
            sel.css('meta[name="ModelName"]::attr(content)').extract_first(),
            sel.css('meta[name="ModelNumber"]::attr(content)').extract_first())
        l.add_value('name', product_name)
        l.add_css('price', 'dd.aftercoupon.value', re='\$(.*)')
        l.add_value('in_stock', True)

        l.add_css('description', '#features>div>div>div.grid_8.alpha')
        l.add_css('details', '#highlights>ul>li')

        time.sleep(2)
        magic_subs = {            # http://www.lenovo.com/images/gallery/1060x596/lenovo-tablet-yoga-8-tilt-mode-6.jpg
            '115x65': '1060x596'  # http://www.lenovo.com/images/gallery/115x65/lenovo-tablet-yoga-8-tilt-mode-6.jpg
        }
        # galleria errors from lenovo's plugin
        image_urls = re.findall(r'Could not extract width/height from image: (http://[^\s]+)\. Traced', response.body)
        new_image_urls = []
        for url in image_urls:
            for before, after in magic_subs.iteritems():
                if url.endswith('jpg') and not 'video' in url:
                    # it just so happens that pngs and gifs are always video
                    # thumbnails that aren't product images
                    new_image_urls.append(url.replace(before, after))

        l.add_value('image_urls', new_image_urls)

        yield l.load_item()
