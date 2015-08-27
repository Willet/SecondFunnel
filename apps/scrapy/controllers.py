from django.core.validators import URLValidator

from scrapy import log, signals
from scrapy.utils.project import get_project_settings
from scrapy.crawler import Crawler
from twisted.internet import reactor

from .spiders import datafeeds, pages

class PageMaintainer(object):
    """
    Controls adding & updating products & content to a page via source urls (or other means?).
    Details of what a specific page can add/update depends on the page & scraper.

    Source urls are category urls, product urls, or some other urls.  The scraper must know
    how to interpret them.

    There are broadly two kinds of scrapers:
        1. Datafeed scrapers
            a. superset - cover many products. They will need to be filtered or matched against
                    products add to a page
            b. set - defines the products on the page and their status

        2. Product url scrapers

    """
    def __init__(self, page):
        self.page = page
        self.store = page.store
        self.feed = page.feed
        self.spider_name = self.feed.spider_name or self.store.slug

        self.url_validator = URLValidator()

    def add(self, source_urls, categories=[], options={}):
        """
        1. Adds new source urls to a page
        2. Scrapes the listed source urls for products & content (depending on scraper)
        3. The products & content scraped are added to categories as tiles (may be existing tiles)

        source_urls: list of <str> urls
        categories: list of <str> catgory names
        options: <dict> which control what is updated IFF implemented for that page
        {
            'spider_name': <str> Over-ride for page / store spider
            'recreate_tiles': <bool> Recreate tiles if they already exist. Wipes old data, categories, etc.
            'skip_images': <bool> Do not scrape product images. Useful if you want a fast data-only update.
            'skip_tiles': <bool> Do not create new tiles if a product or content does not have one already.
        }

        raises: django.core.execeptions.ValidationError for invalid url
        """
        # Ensure source urls look good
        for url in source_urls:
            self.url_validator(url)

        # If source urls are not already in the page, add new source urls
        source_urls = set(source_urls)
        if not source_urls.issubset(set(self.feed.source_urls)):
            self.feed.source_urls = list(set(self.feed.source_urls).union(source_urls))
            self.feed.save()

        # Override for page's spider_name to enable added spider functionality
        spider_name = options.pop('spider_name') if 'spider_name' in options else self.spider_name

        opts = {
            'recreate_tiles': options.get('recreate_tiles', False), # In case you screwed up? Not very useful
            'skip_images': options.get('skip_images', False),
            'skip_tiles': options.get('skip_tiles', False)
        }
        
        self._run_scraper(spider_name=spider_name,
                          start_urls=source_urls,
                          categories=categories,
                          options=opts,
                          project=pages)

    def update(self, options={}):
        """
        Refreshes products and content on a page (depending on scraper).  If a product
        does not get updated, it is set to Out of Stock

        options: <dict> which control what is updated IFF implemented for that page
        {
            'spider_name': <str> Over-ride for page / store spider
            'recreate_tiles': <bool> Recreate tiles the already exist.  Useful for removing out-dated associations & data.
            'skip_images': <bool> Do not scrape product images. Useful if you want a fast data-only update.
            'skip_tiles': <bool> Do not create new tiles if a product or content does not have one already.
        }
        """
        # Add more logic here re start_urls
        if len(self.feed.source_urls):
            start_urls = set(self.feed.source_urls)
        else:
            start_urls = set(self.feed.get_all_products().values_list('url', flat=True))

        # Override for page's spider_name to enable added spider functionality
        spider_name = options.pop('spider_name') if 'spider_name' in options else self.spider_name

        opts = {
            'recreate_tiles': options.get('recreate_tiles', False), # In case you screwed up? Not very useful
            'skip_images': options.get('skip_images', True),
            'skip_tiles': options.get('skip_tiles', True),
            'page_update': True,
        }

        self._run_scraper(spider_name=spider_name,
                          start_urls=start_urls,
                          categories=[],
                          options=opts,
                          project=datafeeds)

    def _run_scraper(self, spider_name, start_urls, categories, options, project):
        """
        set up standard framework for running spider in a script
        """
        settings = self._get_project_settings(project)
        crawler = Crawler(settings)
        crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
        crawler.configure()

        spider = crawler.spiders.create(spider_name, **options)
        spider.start_urls = start_urls
        spider.feed_id = self.feed.id
        spider.categories = categories

        crawler.crawl(spider)
        log.start()
        log.msg('Starting spider with options: {}'.format(options))
        crawler.start()

        reactor.run()

    def _get_project_settings(self, project):
        """
        Scrapers are namespaced by project
        Add in project specific settings & location of scrapers
        """
        settings = get_project_settings()
        settings.setmodule(project)
        settings.setdict({
            'SPIDER_MODULE': [project.__name__],
            'NEWSPIDER_MODULE': project.__name__,
        })
        return settings

