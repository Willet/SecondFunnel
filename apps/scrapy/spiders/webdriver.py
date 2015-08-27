import copy
from scrapy import log
from scrapy.spider import Spider
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


class WebdriverCrawlSpider(Spider, SecondFunnelScraper):
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
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_webdriver.download.WebdriverDownloadHandler',
            'https': 'scrapy_webdriver.download.WebdriverDownloadHandler',
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_webdriver.middlewares.WebdriverSpiderMiddleware': 543,
        },
        # Or any other from selenium.webdriver or 'your_package.CustomWebdriverClass'
        # or an actual class instead of a string.
        'WEBDRIVER_BROWSER': 'PhantomJS',
        # Optional passing of parameters to the webdriver
        'WEBDRIVER_OPTIONS': {
            'service_args': [
                '--debug=true', '--load-images=false', '--webdriver-loglevel=debug'
            ],
        },
    }
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

    def set_crawler(self, crawler):
        super(WebdriverCrawlSpider, self).set_crawler(crawler)
        self._follow_links = crawler.settings.getbool('CRAWLSPIDER_FOLLOW_LINKS', True)


class SecondFunnelCrawlScraper(WebdriverCrawlSpider):
    custom_settings = WebdriverCrawlSpider.custom_settings.copy().update({
        # http://doc.scrapy.org/en/latest/topics/item-pipeline.html#activating-an-item-pipeline-component
        'ITEM_PIPELINES': {
            # 1's - Validation
            'apps.scrapy.pipelines.ForeignKeyPipeline': 1,
            'apps.scrapy.pipelines.ValidationPipeline': 3,
            'apps.scrapy.pipelines.DuplicatesPipeline': 5,
            # 10 - Sanitize and generate attributes
            'apps.scrapy.pipelines.PricePipeline': 11,
            'apps.scrapy.pipelines.ContentImagePipeline': 12,
            # 40 - Persistence-related
            'apps.scrapy.pipelines.ItemPersistencePipeline': 40,
            'apps.scrapy.pipelines.AssociateWithProductsPipeline': 41,
            'apps.scrapy.pipelines.TagPipeline': 42,
            'apps.scrapy.pipelines.ProductImagePipeline': 47,
            # 50 - 
            'apps.scrapy.pipelines.TileCreationPipeline': 50,
            'apps.scrapy.pipelines.SimilarProductsPipeline': 52,
            # 90 - Scrape job control
            'apps.scrapy.pipelines.PageUpdatePipeline': 99,
        },
    })
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
            self.log("Not a product page: {}".format(response.url))
            return []

    def is_product_page(self, response):
        raise NotImplementedError

    def parse_product(self, response):
        raise NotImplementedError

