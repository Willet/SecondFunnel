import re

from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.items import ScraperImage, ScraperProduct
from apps.scrapy.spiders import Rule
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperContentLoader, ScraperProductLoader


class SurLaTableSpider(SecondFunnelCrawlSpider):
    name = 'surlatable'
    root_url = "http://www.surlatable.com"
    allowed_domains = ['surlatable.com']
    store_slug = name

    remove_background = False
    
    # URLs will be scraped looking for more links that match these rules
    rules = (
        # Category page
        Rule(LinkExtractor(allow=[r'surlatable\.com/product/PRO-\d+/?'], restrict_xpaths=
                "//div[contains(@id, 'items')]//dl[contains(@class, 'item')]//a"
            ),
            allow_sources=[r'www\.surlatable\.com/category/'],
            callback="parse_product",
            follow=False),
        # Collection page
        Rule(LinkExtractor(allow=[r'surlatable\.com/product/PRO-\d+/?'], restrict_xpaths=
                "//div[contains(@id, 'items')]//dl[contains(@class, 'item')]//a"
            ),
            allow_sources=[r'www\.surlatable\.com/product/prod\d+/?'],
            callback="parse_product",
            follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(SurLaTableSpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        if self.is_product_page(response):
            return self.parse_product(response)
        elif self.is_recipe_page(response):
            return self.parse_recipe(response)
        else:
            self.logger.info(u"Not a product or recipe page: {}".format(response.url))
            return []

    def is_product_page(self, response):
        #sel = Selector(response)
        #return sel.css('#productdetail label#productPriceValue')
        return bool('surlatable.com/product/PRO-' in response.url)

    def is_recipe_page(self, response):
        # Could be more elaborate, but works
        return bool('surlatable.com/product/REC-' in response.url)

    def is_sold_out(self, response):
        return False

    @staticmethod
    def clean_url(url):
        cleaned_url = re.match(r'((?:http://|https://)?www\.surlatable\.com/(?:category/TCA-\d+|product/(?:REC-|PRO-|prod)\d+)/).*?',
                             url).group(1)
        return cleaned_url

    @staticmethod
    def choose_default_image(product):
        for p in product.product_images.all():
            if not p.is_product_shot:
                return p
        return product.product_images.first()

    def on_product_finished(self, product):
        if self.skip_tiles:
            # update tiles now
            for tile in product.tiles.all():
                self.on_tile_finished(tile, None)

    def on_tile_finished(self, tile, obj):
        """ Set tiles with product shots as their default image to single column """
        try:
            if tile.template == "product":
                if tile.product.default_image.is_product_shot:
                    tile.attributes['colspan'] = 1
                    self.logger.info(u"Setting colspan to 1 for {}".format(tile))
                elif 'colspan' in tile.attributes:
                    del tile.attributes['colspan']
                    self.logger.info(u"Deleting colspan for {}".format(tile))
                tile.save()
        except AttributeError as e:
            self.logger.warning(u"Error determining product shot: {}".format(e))
        
    def parse_product(self, response):
        if not self.is_product_page(response):
            self.logger.info(u"Not a product page: {}".format(response.url))
            return
        
        skip_images = self.skip_images
        skip_tiles = self.skip_tiles
        l.add_value('force_skip_tiles', skip_tiles)

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        attributes = {}
        in_stock = True

        self.if_tagged_product(l, response.meta.get('recipe_id', False))  
        
        l.add_css('name', 'h1#product-title::text')
        l.add_css('description', '#product-description div::text')
        l.add_css('details', '#product-moreInfo-features li')

        # If the page doesn't have a sku, the product doesn't exist
        sku = ''
        try:
            # Try to find the SKU directly, does not work for products with multiple sizes
            sku = sel.css('#product-sku span[itemprop="sku"]::text').extract()[0].strip()
        except (IndexError, AttributeError):
            pass
        if not sku:
            try:
                # could be a color option
                sku = sel.css('#product #product-options a[data-sku]::attr(data-sku)').extract()[0]
            except (IndexError, AttributeError):
                pass
        if not sku:
            try:
                # Product ID usually of form: 'PRO-1220433'
                prod_id = sel.css('#productId::attr(value)').extract()[0]
                sku = re.search(r'\d+', prod_id).group()
            except (IndexError, AttributeError):
                # An item with a missing sku will not validate
                pass
        l.add_value('sku', unicode(sku))

        # prices are sometimes in the forms:
        #    $9.95 - $48.96
        #    Now: $99.96 Was: $139.95 Value: $200.00
        try:
            price_range = sel.css('meta[property="eb:pricerange"]::attr(content)').extract()[0]
            try:
                reg_price = sel.css('.product-priceInfo #product-priceList span::text').extract()[0].split('-')[0]
            except IndexError:
                reg_price = sel.css('.product-priceMain span.hide::text').extract()[0].split('-')[0]
            else:
                sale_price = sel.css('.product-priceMain span.hide::text').extract()[0].split('-')[0]
                l.add_value('sale_price', unicode(sale_price))
            if price_range:
                attributes['price_range'] = unicode(price_range)
        except IndexError:
            in_stock = False
            reg_price = u'$0.00'

        l.add_value('in_stock', in_stock)
        l.add_value('price', unicode(reg_price))
        l.add_value('attributes', attributes)
        l.add_value('url', unicode(response.request.url))
        
        item = l.load_item()

        if skip_images:
            yield item
        else:
            # Full-sized Sur La Table image URLs found in a magical XML file.
            try:
                magic_values = sel.css('.fluid-display::attr(id)').extract_first().split(':')
                xml_path = u"/images/customers/c{1}/{2}/{2}_{3}/pview_{2}_{3}.xml".format(*magic_values)
                request = WebdriverRequest(self.root_url + xml_path, callback=self.parse_product_images)

                request.meta['item'] = item

                yield request
            except IndexError:
                yield item


    def parse_product_images(self, response):
        sel = Selector(response)
        item = response.meta.get('item', ScraperProduct())
        l = ScraperProductLoader(item=item, response=response)

        urls = sel.css('image[url*="touchzoom_variation_Default"]::attr(url)').extract()
        image_urls = set([u'{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1]) for url in urls])
        
        l.add_value('image_urls', image_urls)

        yield l.load_item()

    def parse_recipe(self, response):
        if not self.is_recipe_page(response):
            self.logger.info(u"Not a recipe page: {}".format(response.url))
            return

        recipe_id = re.match(r'(?:http://|https://)?www\.surlatable\.com/product/REC-(\d+)(/.*)?', response.url).group(1)
        sel = Selector(response)

        l = ScraperContentLoader(item=ScraperImage(), response=response)
        l.add_value('force_skip_tiles', self.skip_tiles)
        l.add_value('content_id', recipe_id)
        l.add_value('tag_with_products', True) # Command to AssociateWithProductsPipeline
        l.add_value('original_url', unicode(response.request.url))
        l.add_value('source', 'Sur La Table')
        l.add_css('name', 'h1.name::text')
        l.add_css('description', '#recipedetail .story')
        item = l.load_item()

        if self.skip_images:
            yield item
        else:
            # Continue to XML data to get recipe image
            magic_values = sel.css('.fluid-display::attr(id)').extract_first().split(':')
            xml_path = u'/images/customers/c{1}/{2}/{2}_{3}/pview_{2}_{3}.xml'.format(*magic_values)
            request = WebdriverRequest(self.root_url + xml_path, callback=self.parse_one_image)

            request.meta['item'] = item

            yield request

        # Scrape tagged products
        url_paths = sel.css('.productinfo .itemwrapper>a::attr(href)').extract()
        for url_path in url_paths:
            req = WebdriverRequest(self.root_url + url_path, callback=self.parse_product)
            req.meta['recipe_id'] = recipe_id
            yield req

    def parse_one_image(self, response):
        # For recipes, grab the recipe image
        sel = Selector(response)
        item = response.meta.get('item', ScraperImage())
        l = ScraperContentLoader(item=item, response=response)

        try:
            url = sel.css('image[url*="touchzoom"]::attr(url)').extract()[0]
        except IndexError:
            url = sel.css('image[url*="main"]::attr(url)').extract()[0]
        
        source_url = u'{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1])
        
        l.add_value('source_url', source_url)

        yield l.load_item()
