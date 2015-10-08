import logging
from django.core.validators import URLValidator

from scrapy.utils.project import get_project_settings
from scrapy.crawler import Crawler, CrawlerProcess

from apps.assets.models import Product
from apps.utils.functional import autodiscover_module_classes
from apps.scrapy.spiders.webdriver import SecondFunnelCrawlScraper

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

        2. Page scrapers
            a. product & category urls
            b. content urls (instagram post, blog post, etc)

    """
    def __init__(self, page):
        self.page = page
        self.store = page.store
        self.feed = page.feed
        self.spider_name = self.feed.spider_name or self.store.slug
        logging.debug(u"Initialized {} for {} with spider '{}'".format(self.__class__.__name__,
                                                                      self.page,
                                                                      self.spider_name))
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
            'refresh_images': <bool> Delete existing images & scrape new ones. Wipes old data
            'skip_images': <bool> Do not scrape product images. Useful if you want a fast data-only update.
            'skip_tiles': <bool> Do not create new tiles if a product or content does not have one already.
        }

        raises: django.core.execeptions.ValidationError for invalid url
        """
        logging.debug(u"Adding/updating {} with {} urls".format(self.page, len(source_urls)))

        # Override for page's spider_name to enable added spider functionality
        spider_name = options.pop('spider_name') if 'spider_name' in options else self.spider_name
        spider = self._get_spider(pages, spider_name)

        # Ensure source urls look good
        for url in source_urls:
            self.url_validator(url)
            url = spider.clean_url(url)

        # If source urls are not already in the page, add new source urls
        source_urls = set(source_urls)
        if not source_urls.issubset(set(self.feed.source_urls)):
            self.feed.source_urls = list(set(self.feed.source_urls).union(source_urls))
            self.feed.save()

        opts = {
            'recreate_tiles': options.get('recreate_tiles', False), # In case you screwed up? Not very useful
            'skip_images': options.get('skip_images', False),
            'skip_tiles': options.get('skip_tiles', False)
        }
        
        if options.get('refresh_images', False):
            logging.debug(u"Deleting product images prior to scrape")
            self._delete_product_images(source_urls)

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
        logging.debug(u"Updating {} from datafeed".format(self.page))
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

    def _get_spider(self, project, spidername):
        """Return spider for given spider name"""
        spiders_export = autodiscover_module_classes(project.__name__, project.__path__, SecondFunnelCrawlScraper)
        spiders = dict((x.lower(), y) for x, y in spiders_export)
        return spiders["{}spider".format(spidername)]

    def _run_scraper(self, spider_name, start_urls, categories, options, project):
        """
        set up standard framework for running spider in a script
        """
        settings = self._get_project_settings(project)
        process = CrawlerProcess(settings=settings)
        process.crawl(spider_name,
                      start_urls=start_urls,
                      feed_id=self.feed.id,
                      categories=categories,
                      **options)

        logging.debug(u"Starting scraper with options: {}".format(options))

        process.start()

    def _get_project_settings(self, project):
        """
        Scrapers are namespaced by project
        Add in project specific settings & location of scrapers
        """
        settings = get_project_settings()
        settings.setmodule(project)
        settings.setdict({
            'SPIDER_MODULES': [project.__name__],
            'NEWSPIDER_MODULE': project.__name__,
        })
        return settings

    def _delete_product_images(self, urls):
        for url in urls:
            # This should be unique, but quietly handle multiples
            try:
                ps = Product.objects.filter(url=url, store=self.store)
            except Product.DoesNotExist:
                pass
            else:
                for p in ps:
                    p.in_stock = False # hide product tiles while they have no images
                    p.save()
                    p.product_images.all().delete()
