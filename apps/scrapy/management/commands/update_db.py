from twisted.internet import reactor
from django.core.management.base import BaseCommand
from scrapy import log, signals
from scrapy.utils.project import get_project_settings
from scrapy.crawler import Crawler

from apps.assets.models import Feed, Page

class Command(BaseCommand):
    help = """Rescrapes all products in a given page.
    Usage:
    python manage.py update_db <url_slug> [--tile_template=<tile_template>]

    url_slug
        Url slug of the page to rescrape

    tile_template  # DOES NOT WORK YET
        Whether to create new tiles for scraped products if they don't already exist.
        If provided, create tiles with the specified template. Currently
        just creates product tiles.
    """

    def handle(self, url_slug, **kwargs):
        page = Page.objects.get(url_slug=url_slug)
        feed = page.feed
        store = page.store
        store_slug = store.slug.lower()

        start_urls = []
        for tile in feed.tiles.all():
            if tile.product:
                start_urls.append(tile.product.url)
            for content in tile.content.all():
                for prod in content.tagged_products.all():
                    start_urls.append(prod.url)
        start_urls = set(start_urls)

        # set up standard framework for running spider in a script
        settings = get_project_settings()
        crawler = Crawler(settings)
        crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
        crawler.configure()
            
        spider = crawler.spiders.create(store_slug, **kwargs)
        spider.start_urls = start_urls
        crawler.crawl(spider)
        crawler.start()

        log.start()
        reactor.run()
