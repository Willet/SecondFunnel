import re
from scrapy.contrib.spiders import XMLFeedSpider
from scrapy.http import Request
from scrapy.selector import Selector
from apps.scrapy.items import ScraperProduct
from apps.scrapy.utils import ScraperProductLoader


class VoyagePriveScraper(XMLFeedSpider):
    name = 'voyage-prive'
    allowed_domains = ['officiel-des-vacances.com']
    start_urls = ['http://www.officiel-des-vacances.com/partners/catalog.xml']
    handle_httpstatus_list = [410]

    # XML specific properties
    iterator = 'iternodes'
    itertag = 'node'

    # Custom properties
    categories = [u'10033']

    # TODO: Is there a better way to track id -> name pairings
    categories_dict = {
        u'10033': 'week-end',
        u'10029': 'sejour'
    }
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
        l = ScraperProductLoader(item=ScraperProduct(), selector=node)
        l.add_xpath('sku', 'id/text()')
        l.add_xpath('name', 'titre/text()')
        l.add_xpath('price', 'prix/text()')
        l.add_xpath('in_stock', 'statut/text()')  # TODO: input processor
        l.add_value('url', '')
        # item['url'] = 'http://www.officiel-des-vacances.com/' \
        #               'route-to/{0}/section'.format(item['sku'])

        attributes = {}
        attributes['categories'] = []

        sections = node.xpath('sections/text()').extract_first()
        node_categories = set(sections.split(','))
        scraper_categories = set(self.categories)
        is_part_of_campaign = node_categories.intersection(scraper_categories)

        # TODO: This validation should be left to a pipeline
        if not is_part_of_campaign:
            return

        for category_id in node_categories:
            category = self.categories_dict.get(category_id)
            if not category:
                continue

            attributes['categories'].append((category, None))

        attributes['direct_site_image'] = node.xpath('image-fournisseur/text()').extract_first()
        attributes['direct_site_name'] = node.xpath('nom-fournisseur/text()').extract_first()
        l.add_value('attributes', attributes)

        url = node.xpath('url-detail/text()').extract_first()
        request = Request(url, callback=self.parse_page)

        item = l.load_item()
        request.meta['item'] = item
        return request

    def parse_page(self, response):
        sel = Selector(response)

        item = response.meta['item']
        l = ScraperProductLoader(item=item, response=response)
        l.add_css(
            'image_urls',
            '.viewp-product-pictures-carousel-item img::attr(data-original)'
        )

        attributes = {}
        attributes['review_text'] = sel.css(
            '#viewp-section-push .viewp-product-editorialist blockquote::text'
        ).extract_first()

        attributes['reviewer_name'] = sel.css(
            '#viewp-section-push .viewp-product-owner > a::text'
        ).extract_first()

        attributes['reviewer_image'] = sel.css(
            '#viewp-section-push .viewp-product-editorialist img::attr(src)'
        ).extract_first()

        l.add_value('attributes', item['attributes'])
        l.add_value('attributes', attributes)

        return l.load_item()

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
