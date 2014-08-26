from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule
from scrapy.selector import Selector
from urlparse import urlparse
from urlparse import parse_qs, parse_qsl
from apps.scrapy.items import ScraperProduct
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperProductLoader


class NeweggSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'newegg'
    allowed_domains = ['newegg.com']
    start_urls = ['http://www.newegg.com/']
    rules = [
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//a[contains(@class, "next")]')
        ),
        Rule(
            SgmlLinkExtractor(restrict_xpaths='//div[contains(@class, "itemText")]/div[contains(@class, "wrapper")]/a'),
            'parse_product', follow=False
        )
    ]

    store_slug = name

    def __init__(self, *args, **kwargs):
        if kwargs.get('store_slug'):  # typical use case: 'lenovo'
            self.store_slug = kwargs.get('store_slug')
        super(NeweggSpider, self).__init__(*args, **kwargs)

    def is_product_page(self, response):
        sel = Selector(response)

        is_product_page = sel.css('#singleFinalPrice>span.price-current-label')

        return is_product_page


    def parse_product(self, response):
        """
        Parses a product page on Newegg.com.

        @url http://www.newegg.com/whats-new_clothes/after-party-short-and-sweet-top
        @returns items 1 1
        @returns requests 0 0
        @scrapes url sku name price in_stock description image_urls attributes
        """
        sel = Selector(response)

        url = response.url
        hostname = '{x.scheme}://{x.netloc}'.format(x=urlparse(url))

        # e.g. {'Item': ['N82E16834317541'], 'Tpk': ['34-317-541']}
        params = parse_qs(urlparse(url).query)
        # e.g. {'Item': 'N82E16834317541', 'Tpk': '34-317-541'}
        params = {key: params[key][0] for key in params}

        # figure out product PK in newegg database
        tpk = ''
        if 'Tpk' in params:
            tpk = params['Tpk']
        elif 'Item' in params and len(params['Item']) > 8:
            # reconstruct tpk using the Item key
            tpk = params['Item']
            tpk = tpk[-8:-6] + '-' + tpk[-6:-3] + '-' + tpk[-3:]

        l = ScraperProductLoader(item=ScraperProduct(), response=response)
        l.add_css('url', 'link[rel="canonical"]::attr(href)')
        l.add_value('sku', params['Item'])
        l.add_css('name', '#grpDescrip_{}::text'.format(tpk))
        l.add_value('price', sel.css(
            '#mktplPrice_{} li.price-current strong::text'.format(tpk)
        ).extract_first())
        l.add_value('in_stock', True)

        # * foo
        # * bar
        # * ...
        points = ["<li>{}</li>".format(t.strip())
                  for t in
                  sel.css('#grpBullet_{} li::text'.format(tpk)).extract()]
        points = '<ul>' + ''.join(points) + '</ul>'

        l.add_value('description', points)

        image_urls = sel.css('#pclaImageArea_{} > div > div > ul > li '
                             '> a > img::attr(src)'.format(tpk)).extract()
        # convert thumbs into full urls
        image_urls = [url.replace('$S35$', '$S640$') for url in image_urls]

        l.add_value('image_urls', image_urls)

        # Handle categories
        category_breadcrumb = sel.css('#bcaBreadcrumbTop > dl > dd:nth-child(3) > a')
        category_name = category_breadcrumb.css('::text').extract_first()
        category_url = category_breadcrumb.css('::attr(href)').extract_first()

        attributes = {}
        attributes['categories'] = [(category_name, category_url)]

        # special "newegg" url; matches "url" if product is scraped from newegg
        attributes['neweggUrl'] = sel.css('link[rel="canonical"]::attr(href)').extract_first()
        l.add_value('attributes', attributes)

        yield l.load_item()
