import logging
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

    ### Page routing
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

    def is_category_page(self, response):
        return bool('surlatable.com/category/TCA-' in response.url)

    def is_recipe_page(self, response):
        # Could be more elaborate, but works
        return bool('surlatable.com/product/REC-' in response.url)

    def is_sold_out(self, response):
        return not bool(response.selector.css('#product-actions .product-addToCart').extract_first())

    ### Scraper control
    @staticmethod
    def clean_url(url):
        try:
            return re.match(r'((?:http://|https://)?www\.surlatable\.com/(?:category/TCA-\d+|product/(?:REC-|PRO-|prod)\d+)/).*?',
                             url).group(1)
        except AttributeError:
            # NOTE! only logs outside of scrape process
            logging.error("Could not clean url: {}".format(url))
            return url

    def sort_images_order(self, product_images):
        # Urls have format:
        # http://www.surlatable.com/.../PRO-2166064_pdp/touchzoom_variation_Default_view_4_1700x1700.
        # Need to order them based on view #
        r = re.compile(r"view_(\d+)_\d+x\d+\.$")
        def get_image_number(image):
            try:
                num = r.search(image.original_url).group(1)
            except AttributeError:
                num = 100
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

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('force_skip_tiles', self.skip_tiles)
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
        #    $9.95
        #    $9.95 - $48.96
        #    $99.96  Sugg. $1,860.00 | You save 46%
        price_range = sel.css('meta[property="eb:pricerange"]::attr(content)').extract_first()
        if price_range:
            attributes['price_range'] = price_range

        try:
            price = sel.css('.product-priceMain span.hide::text').extract_first().split('-')[0]
            sugg_price = sel.css('.product-priceInfo #product-priceList span::text').extract_first()
            
            if sugg_price:
                reg_price = sugg_price.split('-')[0] # Sometimes "$9.95 - $48.96"
                sale_price = price
            else:
                reg_price = price
                sale_price = None
            
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

        if self.skip_images:
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
            self.logger.warning(u"Unexpectedly not a recipe page: {}".format(response.request.url))
            return

        recipe_id = re.match(r'(?:http://|https://)?www\.surlatable\.com/product/REC-(\d+)(/.*)?', response.url).group(1)
        sel = Selector(response)

        l = ScraperContentLoader(item=ScraperImage(), response=response)
        l.add_value('force_skip_tiles', self.skip_tiles)
        l.add_value('original_url', unicode(response.request.url))
        l.add_value('source', 'Sur La Table')
        l.add_css('name', 'h1.name::text')
        l.add_css('description', '#recipedetail .story')
        item = l.load_item()

        self.handle_product_tagging(response, item, content_id=recipe_id)

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
            request = WebdriverRequest(self.root_url + url_path, callback=self.parse_product)
            self.prep_product_tagging(request, item)
            yield request

    def parse_one_image(self, response):
        # For recipes, grab the recipe image
        sel = Selector(response)
        item = response.meta.get('item', ScraperImage())
        l = ScraperContentLoader(item=item, response=response)

        url = sel.css('image[url*="touchzoom"]::attr(url)').extract_first() or \
              sel.css('image[url*="main"]::attr(url)').extract_first()
        
        source_url = u'{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1])
        
        l.add_value('source_url', source_url)

        yield l.load_item()
