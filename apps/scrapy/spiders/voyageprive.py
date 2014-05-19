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
        item['store'] = 1

        sections = node.xpath('sections/text()').extract()

        if not sections:
            return

        status = node.xpath('statut/text()').extract()

        node_categories = set(sections[0].split(','))
        scraper_categories = set(self.categories)
        is_part_of_campaign = node_categories.intersection(scraper_categories)
        is_available = self.AVAILABLE_STATUS in status

        if not (is_part_of_campaign and is_available):
            return

        name = node.xpath('titre/text()').extract()
        if name:
            item['name'] = name[0]

        price = node.xpath('prix/text()').extract()[0]
        if price:
            item['price'] = price[0]

        image = node.xpath('image-fournisseur/text()').extract()
        if image:
            item['image_urls'].append(image[0])

        url = node.xpath('url-detail/text()').extract()[0]
        request = Request(url, callback=self.parse_page)
        request.meta['item'] = item
        return request

    def parse_page(self, response):
        sel = Selector(response)

        item = response.meta['item']

        details = sel.css('#viewp-section-push')

        review_text = details.css(
            '.viewp-product-editorialist blockquote::text'
        ).extract()
        if review_text:
            item['attributes']['review_text'] = review_text[0]

        reviewer = details.css('.viewp-product-owner > a::text').extract()
        if reviewer:
            item['attributes']['reviewer_name'] = reviewer[0]

        reviewer_img = details.css(
            '.viewp-product-editorialist img::attr(src)'
        ).extract()
        if reviewer_img:
            item['attributes']['reviewer_img'] = reviewer_img[0]

        # Images are lazy-loaded? Shit.
        product_images = details.css(
            '.viewp-product-pictures-carousel-item img::attr(data-original)'
        ).extract()

        item['image_urls'].extend(product_images)

        return item

    @staticmethod
    def price_pipeline(item, spider):
        return item
