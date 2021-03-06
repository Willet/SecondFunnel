from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from .gap import GapSpider


class OldNavySpider(GapSpider):
    name = 'oldnavy'
    allowed_domains = ['oldnavy.gap.com']
    start_urls = ['http://oldnavy.gap.com/']
    rules = [
        Rule(LinkExtractor(allow=[
            r'/browse/product.do\?.*?pid=\d+'
        ]), 'parse_product', follow=False)
    ]

    store_slug = name

    # see documentation for remove_background in apps.imageservice.tasks
    remove_background = '#FFF'

    root_url = 'http://oldnavy.gap.com'
    category_url = root_url + '/browse/category.do?cid={}'
    product_data_url = root_url + '/browse/productData.do?pid={}'
    visited = []
