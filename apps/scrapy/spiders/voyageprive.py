import re
from scrapy.contrib.spiders import XMLFeedSpider
from scrapy.http import Request
from scrapy.selector import Selector
from apps.scrapy.items import ScraperProduct


class VoyagePriveScraper(XMLFeedSpider):
    name = 'voyage-prive'
    allowed_domains = ['officiel-des-vacances.com']
    start_urls = ['http://www.officiel-des-vacances.com/partners/catalog.xml']
    handle_httpstatus_list = [410]

    # XML specific properties
    iterator = 'iternodes'
    itertag = 'node'

    # Custom properties
    categories = [u'10033'] # 10029 - Sejourner
    store_slug = name
    currency_info = {
        'symbol': u'\u20AC',  # Euro symbol
        'position-at-end': True
    }
    NAME_REGEX = re.compile(r"""(.+),?         # Name of product
                                 \s*            # Followed by 0 or more spaces
                                 (-\s*\d+%)     # Percentage of product off
                              """, re.VERBOSE)
    AVAILABLE_STATUS = u'1'

    def __init__(self, *args, **kwargs):
        super(VoyagePriveScraper, self).__init__(*args, **kwargs)

        if kwargs.get('categories'):
            self.categories = kwargs.get('categories').split(',')

    # Item Loaders can simplify this code even further.
    # However, there are some complications, namely:
    #   - Attributes: Would need a custom item loader
    #   - Fields that depend on fields, but that can be accomplished via
    #     processors:
    #       http://stackoverflow.com/a/19974695
    def parse_node(self, response, node):
        item = ScraperProduct()
        item['attributes'] = {}
        item['image_urls'] = []

        sku = node.xpath('id/text()').extract_first()
        item['sku'] = sku

        sections = node.xpath('sections/text()').extract_first()

        status = node.xpath('statut/text()').extract_first()
        item['in_stock'] = (status == self.AVAILABLE_STATUS)

        node_categories = set(sections.split(','))
        scraper_categories = set(self.categories)
        is_part_of_campaign = node_categories.intersection(scraper_categories)

        # TODO: This validation should be left to a pipeline
        if not is_part_of_campaign:
            return

        item['url'] = 'http://www.officiel-des-vacances.com/' \
                      'route-to/{0}/section'.format(item['sku'])

        name = node.xpath('titre/text()').extract_first()
        if name:
            item['name'] = name

        price = node.xpath('prix/text()').extract_first()
        if price:
            item['price'] = price

        site_image = node.xpath('image-fournisseur/text()').extract_first()
        if site_image:
            item['attributes']['direct_site_image'] = site_image

        site_name = node.xpath('nom-fournisseur/text()').extract_first()
        if site_name:
            item['attributes']['direct_site_name'] = site_name

        url = node.xpath('url-detail/text()').extract_first()
        request = Request(url, callback=self.parse_page)
        request.meta['item'] = item
        return request

    def parse_page(self, response):
        sel = Selector(response)

        item = response.meta['item']

        details = sel.css('#viewp-section-push')

        review_text = details.css(
            '.viewp-product-editorialist blockquote::text'
        ).extract_first()
        if review_text:
            item['attributes']['review_text'] = review_text

        reviewer = details.css('.viewp-product-owner > a::text')\
            .extract_first()
        if reviewer:
            item['attributes']['reviewer_name'] = reviewer

        reviewer_img = details.css(
            '.viewp-product-editorialist img::attr(src)'
        ).extract_first()
        if reviewer_img:
            item['attributes']['reviewer_image'] = reviewer_img

        # Images are lazy-loaded? Shit.
        product_images = details.css(
            '.viewp-product-pictures-carousel-item img::attr(data-original)'
        ).extract()

        item['image_urls'].extend(product_images)

        return item

    @staticmethod
    def name_pipeline(item, spider):
        match = re.match(spider.NAME_REGEX, item['name'])
        if match:
            item['name'] = match.group(1).strip()
            item['attributes']['discount'] = match.group(2)

        # in no position of the product name is "jusqu'a" a useful term to keep
        item['name'] = re.sub(u"jusqu.\u00e0", '', item['name'])
        item['name'] = item['name'].strip(' ,')  # remove spaces, commas, ...

        return item
