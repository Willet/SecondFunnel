import copy
import logging

from scrapy.spiders import Spider
from scrapy.utils.spider import iterate_spider_output
from scrapy_webdriver.http import WebdriverRequest, WebdriverResponse


class SecondFunnelScraper(object):
    def __init__(self, *args, **kwargs):
        super(SecondFunnelScraper, self).__init__(*args, **kwargs)

        # Explicit `start_urls` override other `start_urls`
        if kwargs.get('start_urls'):
            separator = getattr(self, "start_urls_separator", ",")
            self.start_urls = kwargs.get('start_urls').split(separator)

        if kwargs.get('feed_id'):
            self.feed_id = kwargs.get('feed_id')

        if kwargs.get('categories'):
            self.categories = kwargs.get('categories').split(',')

        # Recreate existing tiles
        self.recreate_tiles = kwargs.get('recreate_tiles', False)
        # Skip creation of new tiles
        self.skip_tiles = kwargs.get('skip_tiles', False)
        # Skip processing of images (and if spider supports it, scraping of images)
        self.skip_images = kwargs.get('skip_images', False)
        # For reporting
        self.reporting_name = kwargs.get('reporting_name', '')

    # The functions below are hooks meant to be overwritten 
    # in the spiders for individual clients
    @staticmethod
    def clean_url(url):
        """Hook for cleaning url before scraping
        Returns: cleaned url """
        return url

    @staticmethod
    def choose_default_image(product):
        """Hook for choosing non-product-shot default image on slt
        Returns: image to set as default image, must be one of product_images """
        return product.product_images.first()

    @staticmethod
    def on_product_finished(product):
        """Hook for post-processing a product after scrapy is finished with it"""
        pass

    @staticmethod
    def on_image_finished(image):
        """Hook for post-processing a product after scrapy is finished with it"""
        pass

    @staticmethod
    def on_tile_finished(tile, obj):
        """Hook for post-processing a tile after scrapy is finished with it

        tile - Tile instance
        obj - Either Product or Image instance"""
        pass


class SecondFunnelCrawlScraper(SecondFunnelScraper):
    # These fields are expected to be completed by subclass crawlers
    name = ''
    allowed_domains = []
    store_slug = ''

    # see documentation for remove_background in apps.imageservice.tasks
    remove_background = '#FFF'

    def parse_start_url(self, response):
        if self.is_product_page(response):
            self.rules = ()
            self._rules = []
            return self.parse_product(response)
        else:
            self.logger.info(u"Not a product page: {}".format(response.url))
            return []

    def is_product_page(self, response):
        raise NotImplementedError

    def parse_product(self, response):
        raise NotImplementedError


class WebdriverCrawlSpider(Spider):
    """
    A spider that can automatically crawl other webpages based on rules.

    Duplicates code from scrapy.contrib.spiders.CrawlSpider in order to support
    WebdriverResponse and WebdriverRequest. Why? So that we can scrape
    JavaScript!

    For more details on usage, see:
        http://doc.scrapy.org/en/latest/topics/spiders.html#crawlspider

    Note: Since we've duplicated core code, if we ever update,
    we lose the benefit of the updates. It would be best for us to contibute
    to the project to make the request / response configurable somehow.

    !!! NOTE: Webdriver dies on spiders throwing exceptions: https://github.com/brandicted/scrapy-webdriver/issues/5
              Catch all exceptions and handle gracefull (ugh)
    """
    rules = ()
    request_cls = WebdriverRequest
    response_cls = WebdriverResponse

    def __init__(self, *a, **kw):
        super(WebdriverCrawlSpider, self).__init__(*a, **kw)
        self._compile_rules()

    def _requests_to_follow(self, response):
        # Support WebdriverResponse to allow Javascript scraping
        if not isinstance(response, self.response_cls):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [l for l in rule.link_extractor.extract_links(response) if l not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            seen = seen.union(links)
            for link in links:
                # Use WebdriverRequests to allow Javascript scraping
                r = self.request_cls(url=link.url, callback=self._response_downloaded)
                r.meta.update(rule=n, link_text=link.text)
                yield rule.process_request(r)

    def _parse_response(self, response, callback, cb_kwargs, follow=True):
        if callback:
            cb_res = callback(response, **cb_kwargs) or ()
            cb_res = self.process_results(response, cb_res)
            for requests_or_item in iterate_spider_output(cb_res):
                yield requests_or_item

        if follow and self._follow_links:
            for request_or_item in self._requests_to_follow(response):
                yield request_or_item

    def make_requests_from_url(self, url):
        """Add start_url to child crawlers by default

        http://stackoverflow.com/a/10605941/1558430
        """
        return self.request_cls(url, dont_filter=True, meta={'start_url': url})

    # --------------------------------------------------------------------------
    #   Everything below this line is duplicated verbatim
    #   from scrapy.contrib.spiders.CrawlSpider
    # --------------------------------------------------------------------------
    def parse(self, response):
        return self._parse_response(response, self.parse_start_url, cb_kwargs={}, follow=True)

    def parse_start_url(self, response):
        return []

    def process_results(self, response, results):
        return results

    def _response_downloaded(self, response):
        rule = self._rules[response.meta['rule']]
        return self._parse_response(response, rule.callback, rule.cb_kwargs, rule.follow)

    def _compile_rules(self):
        def get_method(method):
            if callable(method):
                return method
            elif isinstance(method, basestring):
                return getattr(self, method, None)

        self._rules = [copy.copy(r) for r in self.rules]
        for rule in self._rules:
            rule.callback = get_method(rule.callback)
            rule.process_links = get_method(rule.process_links)
            rule.process_request = get_method(rule.process_request)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(WebdriverCrawlSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider._follow_links = crawler.settings.getbool(
            'CRAWLSPIDER_FOLLOW_LINKS', True)
        return spider
