import time
from scrapy_webdriver.http import WebdriverResponse
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper


class PinterestSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'pinterest'
    allowed_domains = ['pinterest.com']
    start_urls = ['http://www.pinterest.com/lecreuset/recettes/']

    # TODO: Handle 'styles'
    visited = []
    rules = []

    def __init__(self, *args, **kwargs):
        super(PinterestSpider, self).__init__(*args, **kwargs)

    # this overrides the regular parse, modifying the response object
    # making sure it has the entire body
    def parse(self, response):
        #
        # trigger infinite scroll until complete
        #
        current_height = response.webdriver.execute_script('return $(document).height()')
        response.webdriver.execute_script('window.scrollBy(0,100000);')
        while True:
            # wait for all ajax requests to complete
            while response.webdriver.execute_script('return $.active') > 0:
                time.sleep(0.1)  # sleep for 100 ms
            new_height = response.webdriver.execute_script('return $(document).height()')
            if new_height > current_height:
                current_height = new_height
                response.webdriver.execute_script('window.scrollBy(0,100000);')
            else:
                break
        print('Pinterest, last height:', current_height)
        new_response = WebdriverResponse(response.url, response.webdriver)
        super(PinterestSpider, self).parse(new_response)


class SurlatablePinterestSpider(PinterestSpider):
    name = 'surlatable_pinterest'
    allowed_domains = ['pinterest.com']
    start_urls = ['http://www.pinterest.com/lecreuset/recettes/']
    rules = []

    store_slug = 'surlatable'
    visited = []

    def parse_start_url(self, response):
        return self.parse_conent(response)

    def parse_content(self, response):
        import pdb; pdb.set_trace()
        sel = Selector(response)
        l = ScraperContentLoader(item=ScraperContent(), response=response)
        l.add_value('url', response.url)
        l.add_css('name', 'h1.name::text')
        l.add_css('description', '#description span.boxsides')
        l.add_value("sku", response.url, re='(\d+)')

        attributes = {}

        sale_price = sel.css('li.sale::text').re_first('(\$\d+\.\d+)')

        if sale_price:
            attributes['sale_price'] = sale_price
            l.add_css('price', 'li.regular::text', re='(\$\d+\.\d+)')
        else:
            l.add_css('price', 'li.price::text', re='(\$\d+\.\d+)')

        l.add_value('attributes', attributes)

        # URL
        magic_values = sel.css('.fluid-display::attr(id)')\
            .extract_first()\
            .split(':')
        xml_path = '/images/customers/c{1}/{2}/' \
            '{2}_{3}/pview_{2}_{3}.xml'.format(*magic_values)

        item = l.load_item()
        request = WebdriverRequest(hostname + xml_path, callback=self.parse_images)

        request.meta['item'] = item

        yield []
