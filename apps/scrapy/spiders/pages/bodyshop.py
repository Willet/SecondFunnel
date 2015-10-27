from scrapy.selector import Selector
from scrapy.spiders import Rule
from scrapy.linkextractors.sgml import SgmlLinkExtractor

from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct


class BodyShopSpider(SecondFunnelCrawlSpider):
    name = 'bodyshop'
    root_url = "http://www.thebodyshop-usa.com"
    allowed_domains = ['thebodyshop-usa.com']
    remove_background = False
    store_slug = name
    # URLs will be scraped looking for more links that match these rules
    rules = (
        # Category page
        Rule(SgmlLinkExtractor(allow=[r'www\.thebodyshop-usa\.com'], restrict_xpaths=
            "//*[@id='fhContentSection']//ul[contains(@class, 'products-list')//span(@class, 'moreDetails')/a"
        ), callback="parse_product", follow=False),
    )

    def __init__(self, *args, **kwargs):
    	super(BodyShopSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        return bool(response.selector.css('div#product-block'))

    def is_sold_out(self, response):
        return bool(response.selector.css('a.outofstockbtn'))

    def parse_product(self, response):
        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        attributes = {}

        l.add_value('url', response.request.url)
        l.add_css('name', 'h1.title::attr(title)')
        l.add_css('description', 'section.product-infos')
        l.add_css('sku', '.volume .title::text', re=r'(\d+)')

        old_price = sel.css('p.price.old::text').extract()
        new_price = sel.css('p.price.new::text').extract()
        if old_price:
            l.add_value('price', old_price[0])
            l.add_value('sale_price', new_price[0])
        else:
            l.add_value('price', new_price[0])

        icons = sel.css('.product_views li[data-type="photo"] img::attr(src)').extract()
        image_urls = []
        for img in icons:
            if self.root_url not in img:
                img = self.root_url + img
            img = img.replace('med_large', 'large').replace('_m_l', '_l')
            image_urls.append(img) 
        l.add_value('image_urls', image_urls)
        
        yield l.load_item()
