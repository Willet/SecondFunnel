import json
import os
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader.processors import TakeFirst, Join
from scrapy.selector import Selector
from urllib import urlencode
from urlparse import parse_qs, urlsplit, urljoin, urlunsplit

from apps.scrapy.spiders import Rule
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlSpider
from apps.scrapy.utils.itemloaders import ScraperProductLoader
from apps.scrapy.items import ScraperProduct


class EBagsSpider(SecondFunnelCrawlSpider):
    name = 'ebags'
    root_url = "http://www.ebags.com"
    allowed_domains = ['ebags.com']
    remove_background = False
    forced_image_ratio = 1.0
    store_slug = name
    # URLs will be scraped looking for more links that match these rules
    rules = (
        # Search, Category, Brand page: product links on current results page
        Rule(LinkExtractor(allow=[r'www\.ebags\.com'], restrict_xpaths=
            "//div[@class='srList']//div[contains(@class, 'listPageItem')]//div[@class='listPageImage']/a",
            ),
            allow_sources=[r"www\.ebags\.com/(?:search/|brand/|category/)"],
            callback="parse_product",
            follow=False),
        # Search, Category, Brand page: follow to next results page
        # canonicalize allows us to follow url fragments like #from120
        Rule(LinkExtractor(allow=[r'www\.ebags\.com'], canonicalize=False, restrict_xpaths=
            "//div[@class='sortbynavbg']//li[@class='pageNext']//a[@class='pagingNext']",
            ),
            allow_sources=[r"www\.ebags\.com/(?:search/|brand/|category/)"],
            follow=True),
    )

    def __init__(self, *args, **kwargs):
        super(EBagsSpider, self).__init__(*args, **kwargs)

    ### Page routing
    def is_product_page(self, response):
        return bool('www.ebags.com/product/' in response.url)

    def is_category_page(self, response):
        return bool(response.selector.css('div.srList'))

    def is_sold_out(self, response):
        return False

    ### Parsers
    def parse_product(self, response):
        sel = Selector(response)
        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        attributes = {}

        l.add_css('url', "link[rel='canonical']::attr(href)")
        sku = sel.css("link[rel='canonical']::attr(href)").re_first(r'/(\d+)$') # use eBags modelId
        l.add_value('sku', sku)
        l.add_css('description', "div.productDetailsCon div.for-jsFeatures ul>li")
        l.add_css('name', "div#productCon h1 span[itemprop='name']::text")

        brand_sel = sel.css("div#productCon h1 a[itemprop='brand']")
        if brand_sel.extract_first():
            brand = {
                'name': brand_sel.css("::attr(content)").extract_first(),
                'url': urljoin(response.url, brand_sel.css("::attr(href)").extract_first()),
            }
            attributes['brand'] = brand

        old_price = sel.css("div#divPricing>div:first-child span.bfx-price::text").extract_first()
        new_price = sel.css("div#divPricing span.pdpFinalPrice::text").extract_first()
        if old_price:
            l.add_value('price', old_price)
            l.add_value('sale_price', new_price)
        else:
            l.add_value('price', new_price)

        l.add_value('attributes', attributes)

        item = l.load_item()

        if self.skip_images:
            yield item
        else:
            # Image urls can take too long to be loaded by JS (resulting in random errors)
            # Get the image ids from eBags data API and build the image urls
            api_url = u"http://externalservice.ebags.com/richmediaservice/api/richmediasets/{}".format(item['sku'])
            request = Request(api_url, callback=self.parse_product_images)
            request.meta['item'] = item
            yield request
    
    def parse_product_images(self, response):
        """
        Response will be json that looks like:
        {
            "Successful":true,
            "RichMediaSet":{
                "ModelId":48439,
                "AssetResourceBaseUri":"http://cdn1.ebags.com/is/image/",
                "CompanyName":"im9",
                "ModelDetailAssets":[
                    "48439_1_2","48439_1_3","48439_1_4","48439_1_5", "48439_1_6","48439_1_7"
                ],
                "DefaultAlternateModelDetailAsset":"48439_1_2",
                "SwatchSetAssets":[
                    "48439_5_1","48439_6_1","48439_7_1","48439_8_1","48439_10_1","48439_11_1",
                    "48439_12_1","48439_13_1","48439_14_1","48439_15_1"
                ],
                "SpinSets":[]
            }
        }
        """
        item = response.meta.get('item', ScraperProduct())
        data = json.loads(response.body)
        if data['Successful']:
            # Got data, build image urls
            assets = data['RichMediaSet']

            img_base_url = urljoin(assets['AssetResourceBaseUri'], assets['CompanyName'])
            first_img = u"{}_1_1".format(assets['ModelId']) # JSON doesn't include 1st image
            img_ids = assets['ModelDetailAssets']
            img_ids.insert(0, first_img)

            item['image_urls'] = [self.generate_image_url(img_base_url, img_id) for img_id in img_ids]
        yield item

    def generate_image_url(self, base_image_url, image_id):
        """
        image urls need to be in this format:
        http://cdn1.ebags.com/is/image/im2/13032_1_2?...
                    ...resmode=4&op_usm=1,1,1,&qlt=80,1&hei=1500&wid=1500&align=0,1&res=1500
        """
        (scheme, netloc, path, _, _) = urlsplit(base_image_url)
        path = os.path.join(path, image_id)
        params = {
            'resmode': 4,
            'op_usm': '1,1,1,',
            'qlt': '80,1',
            'hei': 1500,
            'wid': 1500,
            'align': '0,1',
            'res': 1500,
        }
        qs = urlencode(params, doseq=True)
        url_parts = (scheme, netloc, path, qs, '')
        return urlunsplit(url_parts)
