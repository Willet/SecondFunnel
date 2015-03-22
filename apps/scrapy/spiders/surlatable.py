import re

from scrapy import log
from scrapy.selector import Selector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy_webdriver.http import WebdriverRequest

from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper, WebdriverCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperContentLoader, ScraperProductLoader
from apps.scrapy.items import ScraperImage, ScraperProduct

class SurLaTableSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'surlatable'
    root_url = "http://www.surlatable.com"
    allowed_domains = ['surlatable.com']
    store_slug = name

    remove_background = False

    # URLs will be scraped looking for more links that match these rules
    rules = (
        # Category page
        Rule(SgmlLinkExtractor(allow=[r'surlatable\.com/product/PRO-\d+(/.*)?'], restrict_xpaths=
            "//div[contains(@id, 'items')]/div[contains(@class, 'row')]/dl[contains(@class, 'item')]"
        ), callback="parse_product", follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(SurLaTableSpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        if self.is_sold_out(response):
            # typically on rescraping a product
            raise SoldOut(response.url)
        elif self.is_product_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_product(response)
        elif self.is_recipe_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_recipe(response)
        else:
            self.log("Not a product or recipe page: {}".format(response.url))

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
        
    def parse_product(self, response, force_skip_tiles=False):
        if not self.is_product_page(response):
            log.msg('Not a product page: {}'.format(response.url))
            return


        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        attributes = {}
        in_stock = True
        recipe_id = response.meta.get('recipe_id', False)

        if recipe_id:
            force_skip_tiles = True
            l.add_value('content_id_to_tag', recipe_id)

        # Don't create tiles when gathering products for a recipe
        l.add_value('force_skip_tiles', force_skip_tiles)
        
        l.add_css('name', 'h1.name::text')
        l.add_css('sku', '#productId::attr(value)', re=r'\d+')
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_css('description', '#description .boxsides')

        # prices are sometimes in the forms:
        #    $9.95 - $48.96
        #    Now: $99.96 Was: $139.95 Value: $200.00
        try:
            price_range = sel.css('meta[property="eb:pricerange"]::attr(content)').extract()[0]
            if price_range:
                attributes['price_range'] = price_range
            try:
                reg_price = sel.css('.regular label#productPriceValue::text').extract()[0].split('-')[0]
            except IndexError:
                reg_price = sel.css('.price label#productPriceValue::text').extract()[0].split('-')[0]
            else:
                sale_price = sel.css('.sale label#productPriceValue::text').extract()[0].split('-')[0]
                l.add_value('sale_price', sale_price)
        except IndexError:
            in_stock = False
            reg_price = u'$0.00'

        l.add_value('in_stock', in_stock)
        l.add_value('price', reg_price)
        l.add_value('attributes', attributes)
        item = l.load_item()

        try:
            magic_values = sel.css('.fluid-display::attr(id)').extract_first().split(':')
            xml_path = '/images/customers/c{1}/{2}/{2}_{3}/pview_{2}_{3}.xml'.format(*magic_values)
            request = WebdriverRequest(self.root_url + xml_path, callback=self.parse_product_images)

            request.meta['item'] = item

            yield request
        except IndexError:
            yield item

    def parse_product_images(self, response):
        sel = Selector(response)
        item = response.meta.get('item', ScraperProduct())
        l = ScraperProductLoader(item=item, response=response)

        urls = sel.css('image[url*="touchzoom"]::attr(url)').extract()
        image_urls = set(['{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1]) for url in urls])
        
        l.add_value('image_urls', image_urls)

        yield l.load_item()

    def parse_recipe(self, response):
        if not self.is_recipe_page(response):
            log.msg('Not a recipe page: {}'.format(response.url))
            return

        recipe_id = re.match(r'(?:http://|https://)?www\.surlatable\.com/product/REC-(\d+)(/.*)?', response.url).group(1)
        sel = Selector(response)

        l = ScraperContentLoader(item=ScraperImage(), response=response)
        l.add_value('content_id', recipe_id)
        l.add_value('tag_with_products', True) # Command to TagWithProductsPipeline
        l.add_value('original_url', response.url)
        l.add_value('source', 'Sur La Table')
        l.add_css('name', 'h1.name::text')
        l.add_css('description', '#recipedetail .story')
        item = l.load_item()

        # Continue to XML data to get recipe image
        magic_values = sel.css('.fluid-display::attr(id)').extract_first().split(':')
        xml_path = '/images/customers/c{1}/{2}/{2}_{3}/pview_{2}_{3}.xml'.format(*magic_values)
        request = WebdriverRequest(self.root_url + xml_path, callback=self.parse_one_image)

        request.meta['item'] = item

        yield request

        # Scrape associated products
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

        url = sel.css('image[url*="touchzoom"]::attr(url)').extract()[0]
        source_url = '{}/{}'.format(response.url.rsplit('/', 1)[0], url.rsplit('/', 1)[1])
        
        l.add_value('source_url', source_url)

        yield l.load_item()
