from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy_webdriver.action_chains import WaitingActionChains
from scrapy_webdriver.http import WebdriverRequest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders import Rule
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class BodyShopSpider(SecondFunnelCrawlSpider):
    name = 'bodyshop'
    root_url = "http://www.thebodyshop-usa.com"
    allowed_domains = ['thebodyshop-usa.com']
    remove_background = False
    forced_image_ratio = 1.0
    store_slug = name
    # URLs will be scraped looking for more links that match these rules
    rules = (
        # Category page, follow these links
        Rule(LinkExtractor(allow=[r'www\.thebodyshop-usa\.com'], restrict_xpaths=
            "//*[@id='fhContentSection']//ul[contains(@class, 'products-list')]//span[contains(@class,'moreDetails')]/a"
        ), callback="parse_product", follow=False),
    )

    def __init__(self, *args, **kwargs):
    	super(BodyShopSpider, self).__init__(*args, **kwargs)

    ### Page routing
    def is_product_page(self, response):
        return bool(response.selector.css('div#product-block'))

    def is_category_page(self, response):
        return bool(response.selector.css('ul.products-list'))

    def is_sold_out(self, response):
        style = response.selector.css('a.outofstockbtn::attr(style)').extract_first()
        return not bool('display' in style and 'none' in style)

    ### Parses
    def parse_product(self, response):
        if not self.is_product_page(response):
            self.logger.warning(u"Unexpectedly not a product page: {}".format(response.request.url))
            return

        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)

        l.add_value('force_skip_tiles', self.skip_tiles)
        l.add_value('attributes', {})
        l.add_value('in_stock', bool(not self.is_sold_out(response)))
        l.add_css('url', "link[rel='canonical']::attr(href)")
        l.add_css('name', 'h1.title::attr(title)')
        l.add_css('sku', '.itemQuantitySection .title::text', re=r'(\d+)')
        # description is <p>'s followed by an <ul>
        # 1st <p> is "PRODUCT DESCRIPTION", 2nd is *usually* the introduction, but occasionally
        # its empty and the introduction is in the 3rd <p>
        description = (sel.xpath("//section[@class='product-infos']/p[position()=2]/text()").extract()
                    or sel.xpath("//section[@class='product-infos']/p[position()=3]/text()").extract())
        l.add_value('description', description)

        old_price = sel.css('p.price.old::text').extract()
        new_price = sel.css('p.price.new::text').extract()
        value = sel.css('.priceOffersSection #product-offers').re_first(r'\$(\d+) Value')
        if old_price or value:
            l.add_value('price', (old_price or value))
            l.add_value('sale_price', new_price)
        else:
            l.add_value('price', new_price)

        icons = sel.css('.product_views li[data-type="photo"] img::attr(src)').extract()
        image_urls = []
        for img in icons:
            if self.root_url not in img:
                img = self.root_url + img
            img = img.replace('med_large', 'large').replace('_m_l', '_l')
            image_urls.append(img) 
        l.add_value('image_urls', image_urls)
        item = l.load_item()
        
        self.handle_product_tagging(response, item, product_id=item['url'])
        
        yield item

        if item.get('tag_with_products', False):
            # Wait for recommended products to load
            try:
                actions = WaitingActionChains(response.webdriver).wait(60, name='presence_of_element_located',
                            args=[(By.CSS_SELECTOR, "article.top-products")]).perform()
            except TimeoutException:
                self.logger.warning(u"Timeout before getting similar products: {}".format(response.request.url))
                pass
            else:
                request = response.action_request(actions=actions, callback=self.parse_recommended_products)
                request.meta['item'] = item
                yield request

    def parse_recommended_products(self, response):
        # Scrape similar products
        sel = Selector(response)
        url_paths = sel.css('article.top-products .content>a::attr(href)').extract()
        for url_path in url_paths:
            request = WebdriverRequest(url_path, callback=self.parse_product)
            self.prep_product_tagging(request, response.meta.get('item'))
            yield request
