from django.core.management.base import BaseCommand
from optparse import make_option
from scrapy import log, signals
from scrapy.utils.project import get_project_settings
from scrapy.crawler import Crawler
from twisted.internet import reactor

from apps.assets.models import Feed, Page

class Command(BaseCommand):
    help = """Rescrapes all products in a given page.
    Usage:
    python manage.py update_db [-t, --recreate-tiles] [-i, --update-images] <url_slug>

    url_slug
        Url slug of the page to rescrape

    -t, --recreate_tiles
        Recreate tiles the already exist.  Useful for removing out-dated associations & data.

    -i, --update-images
        Scrape product images.
    """
    option_list = BaseCommand.option_list + (
            make_option('-t','--recreate-tiles',
                action="store_true",
                dest="recreate_tiles",
                default=False,
                help="Recreate all tiles."),
            make_option('-i','--update-images',
                action="store_true",
                dest="update_images",
                default=False,
                help="Scrape product images."),
        )

    def handle(self, url_slug, **options):
        page = Page.objects.get(url_slug=url_slug)
        feed = page.feed
        store = page.store
        store_slug = store.slug.lower()
        opts = {
            'recreate_tiles': options['recreate_tiles'],
            'skip_images': not options['update_images'],
            'skip_tiles': True,
        }
        
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

        spider = crawler.spiders.create(store_slug, **opts)
        spider.start_urls = start_urls
        spider.feed_ids = [feed.id]

        crawler.crawl(spider)
        log.start()
        log.msg('Starting spider with options: {}'.format(opts))
        crawler.start()

        reactor.run()
