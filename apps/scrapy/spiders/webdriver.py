import copy

from scrapy.spiders import Spider
from scrapy.utils.spider import iterate_spider_output
from scrapy_webdriver.http import WebdriverRequest, WebdriverResponse

from .mixins import ProcessingMixin


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

    def __init__(self, *args, **kwargs):
        super(WebdriverCrawlSpider, self).__init__(*args, **kwargs)
        self._compile_rules()

    def _requests_to_follow(self, response):
        # Support WebdriverResponse to allow Javascript scraping
        if not isinstance(response, self.response_cls):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            if not rule.source_allowed(response.url):
                # This rule is skipped for this request url
                continue
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


class SecondFunnelCrawlSpider(WebdriverCrawlSpider, ProcessingMixin):
    """
    A base spider for Second Funnel Use
    """
    # These fields are expected to be completed by subclass crawlers
    name = ''
    allowed_domains = []
    store_slug = ''

    # see documentation for remove_background in apps.imageservice.tasks
    remove_background = '#FFF'

    def __init__(self, *args, **kwargs):
        # Set Options:
        # Feed to add tiles to:
        self.feed_id = kwargs.pop('feed_id', None)
        # Categories to add tiles to:
        self.categories = kwargs.pop('categories', None)
        if self.categories:
            self.categories = self.categories.split(',')
        # Recreate existing tiles
        self.recreate_tiles = kwargs.pop('recreate_tiles', False)
        # Skip creation of new tiles
        self.skip_tiles = kwargs.pop('skip_tiles', False)
        # Skip processing of images (and if spider supports it, scraping of images)
        self.skip_images = kwargs.pop('skip_images', False)
        # For reporting
        self.reporting_name = kwargs.pop('reporting_name', '')

        super(SecondFunnelCrawlSpider, self).__init__(*args, **kwargs)

    def parse_start_url(self, response):
        """
        Over-write to add more types of start-urls
        """
        if self.is_product_page(response):
            return self.parse_product(response)
        elif self.is_category_page(response):
            # Don't scrape category pages
            return []
        else:
            self.logger.error(u"Unrecognized start url: {}".format(response.url))
            return []

    def is_product_page(self, response):
        raise NotImplementedError

    def is_category_page(self, response):
        raise NotImplementedError

    def parse_product(self, response):
        raise NotImplementedError
