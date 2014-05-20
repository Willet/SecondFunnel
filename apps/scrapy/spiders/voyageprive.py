from scrapy.contrib.spiders import XMLFeedSpider
from scrapy.http import Request
from scrapy.selector import Selector
from apps.scrapy.items import ScraperProduct


class VoyagePriveScraper(XMLFeedSpider):
    name = 'voyageprive'
    allowed_domains = ['officiel-des-vacances.com']
    start_urls = ['http://www.officiel-des-vacances.com/partners/catalog.xml']
    handle_httpstatus_list = [410]

    # XML specific properties
    iterator = 'iternodes'
    itertag = 'node'

    # Custom properties
    categories = [u'10033'] # 10029 - Sejourner
    store_slug = name
    AVAILABLE_STATUS = u'1'

    def __init__(self, *args, **kwargs):
        super(VoyagePriveScraper, self).__init__(*args, **kwargs)

        if kwargs.get('categories'):
            self.categories = kwargs.get('categories').split(',')


    # TODO: Why do we always have to access the first element?
    # Is there a way to do so by default?
    def parse_node(self, response, node):
        # name, price, image_urls
        item = ScraperProduct()
        item['attributes'] = {}
        item['image_urls'] = []

        sku = node.xpath('id/text()').extract_first()
        if not sku:
            return

        item['sku'] = sku

        sections = node.xpath('sections/text()').extract_first()

        if not sections:
            return

        status = node.xpath('statut/text()').extract_first()

        node_categories = set(sections.split(','))
        scraper_categories = set(self.categories)
        is_part_of_campaign = node_categories.intersection(scraper_categories)
        is_available = self.AVAILABLE_STATUS in status

        if not (is_part_of_campaign and is_available):
            return

        item['url'] = 'http://www.officiel-des-vacances.com/' \
                      'route-to/{0}/section'.format(item['sku'])

        name = node.xpath('titre/text()').extract_first()
        if name:
            item['name'] = name

        price = node.xpath('prix/text()').extract_first()
        if price:
            item['price'] = price

        image = node.xpath('image-fournisseur/text()').extract_first()
        if image:
            item['image_urls'].append(image)

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
            item['attributes']['reviewer_img'] = reviewer_img

        # Images are lazy-loaded? Shit.
        product_images = details.css(
            '.viewp-product-pictures-carousel-item img::attr(data-original)'
        ).extract()

        item['image_urls'].extend(product_images)

        return item

    @staticmethod
    def price_pipeline(item, spider):
        item['price'] = '$' + item['price']
        return item
