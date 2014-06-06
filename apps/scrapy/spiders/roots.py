import re
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverRequest
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, SecondFunnelScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class RootsSpider(SecondFunnelScraper, WebdriverCrawlSpider):
    name = 'roots'
    allowed_domains = ['usa.roots.com', 'canada.roots.com']
    start_urls = ['http://usa.roots.com/women/best-sellers/womensBestSellers,default,sc.html']
    start_urls_separator = "|"  # because urls above contain commas,
                                # now you need to separate urls in the terminal
                                # using this symbol.
    rules = [
        Rule(SgmlLinkExtractor(allow=[r'pd.html']),
             callback='parse_product',
             follow=False)
    ]

    store_slug = name

    def parse_start_url(self, response):
        if self.is_product_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_product(response)

        return []

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('#productdetails .key')

        return is_product_page

    def parse_product(self, response):
        """
        Parses a product page on Roots.com.

        @url http://canada.roots.com/SmallBanffBagHorween/LeatherLuggageBags//18040023,default,pd.html?cgid=leatherWeekenderBags&selectedColor=Z65
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price description image_urls attributes
        """
        def full_size_image(x):
            """From
            thumb_variation_A59_view_b_55x55.jpg
            to
            main_variation_A59_view_b_579x579.jpg

            (and pray that all their images are all 579 pixels wide)
            """
            return 'main_variation_{}_view_{}_579x579.jpg'.format(x.group(1), x.group(2))

        full_url_format = "http://demandware.edgesuite.net/aacg_prd/on/" \
                          "demandware.static/Sites-RootsCA-Site/" \
                          "Sites-roots_master_catalog/default/" \
                          "v1401786139656/customers/c972/{pid}/{pid}_pdp2/" \
                          "main_variation_{sc}_view_a_579x579.jpg"

        sel = Selector(response)

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_value('url', response.url)
        l.add_css('sku', '#productdetails .key::text', re='(\d+)')
        l.add_css('name', '#productName::text')

        # TODO: Sanitize output with bleach
        l.add_css('description', '.prodctdesc .description::text')

        # TODO: WTF does this need to be this complicated?
        image_urls = []
        img_thumbs = sel.xpath('//div[contains(@class, "fluid-display-imagegroup")]//img[contains(@class, ":view")]')
        selectedColor = re.findall(r"var\s?selectedColor\s?=\s?\'(\w+)\';", response.body, re.I | re.M | re.U)

        for thumb in img_thumbs:
            thumb_url = thumb.css('::attr(src)').extract_first()
            if thumb_url:
                full_url = re.sub(r'thumb_variation_(\w\d+)_view_(\w)_\d+x\d+\.jpg', full_size_image, thumb_url)
            else:
                # wild(er) guess if JS is behind
                # (hopefully it won't have to come to this)
                if selectedColor:
                    # construct unverified image url using default color ID
                    product_image_pid = re.findall(r':view:\d+:(\d+):pdp2', thumb.extract())[0]
                    full_url = full_url_format.format(
                        pid=product_image_pid, sc=selectedColor[0])

            if not full_url:
                continue
            image_urls.append(full_url)

        if not image_urls and selectedColor:
            # wild guess (2) for pages that have only one image and no "picker"
            default_pic_id = sel.css('.fluid-display::attr(id)').extract_first()
            product_image_pid = re.findall(r'display:\d+:(\d+):pdp2',
                                           default_pic_id)[0]
            image_urls.append(full_url_format.format(pid=product_image_pid, sc=selectedColor[0]))

        attributes = {}
        sale_price = sel.css('.pricing #priceTop .special .value::text').extract_first()

        if not sale_price:
            l.add_css('price', '.pricing #priceTop .value::text')
        else:
            l.add_css('price', '.pricing #priceTop .standard .value::text')
            attributes['sale_price'] = sale_price

        attributes['categories'] = []
        category_sels = sel.css('.breadcrumbs').xpath('a[@href!="#"]')
        for category_sel in category_sels:
            category_url = category_sel.css('::attr(href)').extract_first()
            category_name = category_sel.css('::text').extract_first().strip()
            attributes['categories'].append((category_name, category_url))

        l.add_value('image_urls', image_urls)
        l.add_value('attributes', attributes)

        yield l.load_item()
