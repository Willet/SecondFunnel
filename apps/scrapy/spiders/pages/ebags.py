from scrapy.linkextractors import LinkExtractor
from scrapy.loader.processors import TakeFirst, Join
from scrapy.selector import Selector
from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit

from apps.scrapy.spiders import Rule
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct


class EBagsSpider(SecondFunnelCrawlSpider):
    name = 'ebags'
    root_url = "http://www.ebags.com"
    allowed_domains = ['ebags.com']
    remove_background = False
    store_slug = name
    # URLs will be scraped looking for more links that match these rules
    rules = (
        # Search page, Brand page, follow these links
        Rule(LinkExtractor(allow=[r'www\.thebodyshop-usa\.com'], restrict_xpaths=
            "//div[@class='srList']//div[contains(@class, 'listPageItem')]//div[@class='listPageImage']/a",
            allow_sources=[r"www\.ebags\.com/(?:search/|search/|brand/|category/)"],
        ), callback="parse_product", follow=False),
    )

    def __init__(self, *args, **kwargs):
        super(EBagsSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        return bool(response.selector.css('div.add-cart-con'))

    def is_sold_out(self, response):
        return False

    def parse_product(self, response):
        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        attributes = {}

        l.add_value('url', response.request.url)
        l.add_css('description', "div.productDetailsCon div[itemprop='description']::text")
        l.add_css('sku', 'div#productSpecificationSku + div.specs::text')

        brand = sel.css("div.productCon h1 a[itemprop='brand']::attr(content)", TakeFirst())
        name = sel.css("div.productCon h1 span[itemprop='name']::text", TakeFirst())
        l.add_value('name', [brand, name], Join())

        old_price = sel.css("div#divPricing>div:first-child span.bfx-price::text").extract_first()
        new_price = sel.css("div#divPricing span.pdpFinalPrice::text").extract_first()
        if old_price:
            l.add_value('price', old_price)
            l.add_value('sale_price', new_price)
        else:
            l.add_value('price', new_price)

        
        icons = sel.css("div#richMediaIcons>img.iconImage::attr(src)").extract()
        image_urls = []
        for img in icons:
            image_urls.append(update_image_url(img))
        l.add_value('image_urls', image_urls)
        
        yield l.load_item()

    def update_image_url(self, url):
        """
        image urls come in format:
        http://cdn1.ebags.com/is/image/im2/13032_1_2?resmode=4&op_usm=1,1,1,&qlt=95,1&hei=65&wid=65&align=0,1
        need to convert url params to: ?resmode=4&op_usm=1,1,1,&qlt=80,1&hei=1500&wid=1500&align=0,1&res=1500
        """
        scheme, netloc, path, query_string, fragment = urlsplit(url)
        query_params = parse_qs(query_string)

        query_params.update({
            'resmode': 4,
            'op_usm': '1,1,1,',
            'qlt': '80,1',
            'hei': 1500,
            'wid': 1500,
            'align': '0,1',
            'res': 1500,
        })
        updated_qs = urlencode(query_params, doseq=True)
        return urlunsplit((scheme, netloc, path, updated_qs, fragment))
