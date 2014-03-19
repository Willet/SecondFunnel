from scrapy.spider import Spider
from scrapy.selector import HtmlXPathSelector

from apps.scraper.scrapers.gap.items import GapProduct


class GapProductSpider(Spider):
    name = "gap-product-spider"
    allowed_domains = ["gap.com"]
    start_urls = [
        "http://www.gap.com/browse/product.do?pid=942057",
    ]

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        sites = hxs.select('//ul[@class="directory-url"]/li')
        items = []

        for site in sites:
            item = GapProduct()
            item['name'] = site.select('span[contains(@class, productName)]').extract()
            items.append(item)

        return items