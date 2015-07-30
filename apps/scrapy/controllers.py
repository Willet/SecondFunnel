from scrapy import log, signals
from scrapy.utils.project import get_project_settings
from scrapy.crawler import Crawler
from twisted.internet import reactor


class PageUpdater(object):
    """
    Updates the products, tiles (& sometimes content) on a page.  Details it does this depends on the
    page & scraper.


    There are 2 ways to specify a feed:

    1. Category list  - products are specified by category identifiers (urls, names, ids, etc).
        Get a current list of products in the category & update the page appropriately.

    2. Product list - products are specified by a list of product identifiers (urls, names, ids, etc).
        Update them appropriately.

    There are 2 ways to get the data to update:

        1. Datafeeds
            a. superset - cover many products. They will need to be filtered or matched against products
            b. set - defines the products on the page and their status

        2. Scrape product urls

    Every update is a combination of the above.
    """
    def __init__(self, page):
        self.page = page
        self.store = page.store
        self.feed = page.feed

    def run(self, options):
        """
        options: <dict> which control what is updated IFF implemented for that page
        {
            'recreate_tiles': <bool> Recreate tiles the already exist.  Useful for removing out-dated associations & data.
            'skip_images': <bool> Do not scrape product images. Useful if you want a fast data-only update.
            'skip_tiles': <bool> Do not create new tiles if a product or content does not have one already.
        }
        """
        # Add more logic here re start_urls
        if source_urls in page.attributes:
            start_urls = page.attributes.source_urls
        else:
            start_urls = set(self.feed.get_all_products().values_list('url', flat=True))

        # More logic could be added here regarding spider_name if it arises
        if spider_name in page.attributes:
           spider_name = page.attributes.spider_name
        else:
            spider_name = self.store_slug

        self._run_scraper(spider_name=spider_name,
                          start_urls=start_urls,
                          feed_ids=[self.feed.id],
                          options=opts)

    def _run_scraper(self, spider_name, start_urls, feed_ids, options):
        # set up standard framework for running spider in a script
        settings = get_project_settings()
        crawler = Crawler(settings)
        crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
        crawler.signals.connect(self.update_tiles, signal=signals.spider_closed)
        crawler.configure()

        spider = crawler.spiders.create(spider_name, **options)
        spider.start_urls = start_urls
        spider.feed_ids = feed_ids

        crawler.crawl(spider)
        log.start()
        log.msg('Starting spider with options: {}'.format(opts))
        crawler.start()

        reactor.run()

    def _update_tiles(self, spider, reason):
        """
        Update the IR cache now that products are updated
        """
        self.feed.update_tiles_ir_cache()

