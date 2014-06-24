import time
from scrapy.selector import Selector
from scrapy_webdriver.http import WebdriverResponse
from apps.scrapy.spiders.webdriver import WebdriverCrawlSpider, \
    SecondFunnelCrawlScraper
from apps.scrapy.utils.itemloaders import ScraperContentLoader
from apps.scrapy.items import ScraperImage


class PinterestSpider(SecondFunnelCrawlScraper, WebdriverCrawlSpider):
    name = 'pinterest'
    allowed_domains = ['pinterest.com']
    start_urls = []

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
        return super(PinterestSpider, self).parse(new_response)

    def parse_start_url(self, response):
        return self.parse_content(response)

    def parse_content(self, response):
        sel = Selector(response)
        pin_selectors = sel.css('.item .pinWrapper')
        for pin_selector in pin_selectors:
            l = ScraperContentLoader(item=ScraperImage(), selector=pin_selector)
            l.add_css('name', '.richPinGridTitle::text')
            l.add_css('description', '.pinDescription::text')
            l.add_value('original_url', response.url)
            l.add_value('source', 'pinterest')
            image_url = pin_selector.css('.pinImg::attr(src)').extract_first()
            image_url = image_url.replace('/236x/', '/1200x/')
            l.add_value('source_url', image_url)
            item = l.load_item()
            yield item


class SurlatablePinterestSpider(PinterestSpider):
    name = 'surlatable_pinterest'
    allowed_domains = ['pinterest.com']
    start_urls = ['http://www.pinterest.com/lecreuset/recettes/']
    rules = []

    store_slug = 'surlatable'
    visited = []
