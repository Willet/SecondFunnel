#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import logging
import re
from urlparse import urlsplit, urlunsplit, urljoin
from w3lib.html import remove_tags

from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.loader.processors import Join, TakeFirst
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.items import ScraperImage, ScraperProduct
from apps.scrapy.spiders import Rule
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperContentLoader, ScraperProductLoader
from apps.scrapy.utils.misc import normalize_price


class CB2Spider(SecondFunnelCrawlSpider):
    name = 'cb2'
    root_url = "http://www.cb2.com"
    allowed_domains = ['cb2.com']
    store_slug = name

    remove_background = False
    forced_image_ratio = 1
    
    # URLs will be scraped looking for more links that match these rules
    rules = ()

    def __init__(self, *args, **kwargs):
        super(VanHarenSpider, self).__init__(*args, **kwargs)

    ### Page routing
    def parse_start_url(self, response):
        if self.is_product_page(response):
            return self.parse_product(response)
        else:
            self.logger.info(u"Not a product page: {}".format(response.url))
            return []

    def is_product_page(self, response):
        # works for both simple product pages and furniture select pages
        return bool(response.selector.css('#bodyWrap #main>.product').extract_first())
        return 

    def is_category_page(self, response):
        # Not the best selector...
        return bool(response.selector.css('#bodyWrap>.spill').extract_first())

    def is_sold_out(self, response):
        # standard product page
        in_stock_simple_product = bool(response.selector.css('.shopBtns a.jsAddToCart').extract_first())
        # product with options page
        in_stock_furniture_select = bool(response.selector.css('.shoppingBar a.jsAddToCart').extract_first())
        return not (in_stock_simple_product or in_stock_furniture_select)

    ### Scraper control
    @staticmethod
    def clean_url(url):
        try:
            clean_url = re.match(r'((?:http://|https://)?www\.vanharen\.nl/NL/nl/shop/\d+/[\w*%-]+\.prod).*?', url).group(1)
            # For reasons unknown, scrapes of https pages return the previous response...
            return clean_url.replace('https', 'http', 1)
        except AttributeError:
            # NOTE! only logs outside of scrape process
            logging.error("Could not clean url: {}".format(url))
            return url

    def sort_images_order(self, product_images):
        # Urls have format:
        # http://deichmann.scene7.com/asset/deichmann/p_100/--1341724_P2.png
        # Need to order them based on P#: P, P1, P2, etc
        r = re.compile(r"deichmann\.scene7\.com/asset/deichmann/p_100/--\d+_P(\d)?\.(?:jpg|png)")
        def get_image_number(image):
            try:
                num = r.search(image.original_url).group(1)
            except AttributeError:
                num = 100
            else:
                if not num:
                    # 1st image is just P -> num = None
                    num = 0
            return int(num)

        return sorted(product_images, key=get_image_number)

    def choose_default_image(self, product):
        images = self.sort_images_order(product.product_images.all())
        return images[0]

    def on_product_finished(self, product):
        if not self.skip_images:
            sorted_images = self.sort_images_order(product.product_images.all())
            product.attributes['product_images_order'] = [i.id for i in sorted_images]
            product.save()

        if self.skip_tiles:
            # update tiles now
            for tile in product.tiles.all():
                self.on_tile_finished(tile, None)

    def on_tile_finished(self, tile, obj):
        """ Set tiles with product shots as their default image to single column """
        try:
            if not tile.placeholder and tile.template == "product":
                if tile.product.default_image.is_product_shot:
                    tile.attributes['colspan'] = 1
                    self.logger.info(u"Setting colspan to 1 for {}".format(tile))
                elif 'colspan' in tile.attributes:
                    del tile.attributes['colspan']
                    self.logger.info(u"Deleting colspan for {}".format(tile))
                tile.save()
        except AttributeError as e:
            self.logger.warning(u"Error determining product shot: {}".format(e))
    
    ### Parsers
    def parse_product(self, response):
        if not self.is_product_page(response):
            self.logger.warning(u"Unexpectedly not a product page: {}".format(response.request.url))
            return
        
        attributes = {}

        sel = response.selector
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('force_skip_tiles', self.skip_tiles)

        if bool(sel.css('#bodyWrap #pageWrap.product').extract_first()):
            # standard product page
            l.add_css('name', '.productImgContainer h1#_productTitle::text')
            l.add_css('description', '.productDescriptionContainer p#_productDescription')
            l.add_css('sku', '.productDescriptionContainer span#_skuNum::text')
        else:
            # product with options page
            l.add_css('name', '#productViewWrap h1#productNameHeader::text')
            l.add_css('description', '')
            l.add_css('sku', '')

        try:
            price = l.get_css("metaa[property=og:price:amount]::attr(content)", TakeFirst())
            reg_price = l.get_css("metaa[property=og:price:standard_amount]::attr(content)", TakeFirst())
            if reg_price:
                sale_price = price
            else:
                sale_price = None
                reg_price = price
            
        except IndexError:
            reg_price = u'$0.00'
            sale_price = None

        l.add_value('in_stock', bool(not self.is_sold_out(response)))
        l.add_value('price', unicode(reg_price))
        l.add_value('sale_price', unicode(sale_price) if sale_price else None)
        l.add_value('attributes', attributes)
        l.add_value('url', unicode(response.request.url))

        item = l.load_item()

        # If this is a similar_product and tagged_product, handle it
        self.handle_product_tagging(response, item)

        if not self.skip_images:
            urls = sel.css('.productImgContainer .productImageSelection li img::attr(src)').extract()
            image_urls = set([self.generate_image_url(u) for u in urls])
            item['image_urls'] = image_urls

        return item

    def generate_image_url(self, url):
        """
        url looks like: 
          http://images.cb2.com/is/image/CB2/GlobePendantLightAV2S16/$web_zoom$&wid=50&hei=50/151023134026/globe-pendant-light.jpg
        Need to remove "&wid=50&hei=50"
        """
        (scheme, netloc, path, _, _) = urlsplit(url)
        path = re.sub(r'\$web_zoom\$wid=\d+\&hei=\d+', '$web_zoom$', path)
        url_parts = (scheme, netloc, path, '', '')
        return urlunsplit(url_parts)
