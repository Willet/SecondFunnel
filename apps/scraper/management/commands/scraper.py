import json
from os.path import join, dirname

from optparse import make_option
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.assets.models import Store, Page, Feed
from apps.pinpoint.utils import read_a_file
from apps.scraper.scrapers.scraper import CloudScraper


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--store-id', default=None),
        make_option('--url', default=None),
        make_option('--page-slug', default=None),
        make_option('--folder', default=None))  # --folder is deprecated

    def handle(self, *args, **kwargs):
        """
        If called with store-id (somehow) and url, scrapes that url for
            that store.
        Otherwise, scrapes all urls listed in all text files in the urls folder.
        """
        store_id = kwargs.pop('store_id', None)
        page_slug = kwargs.pop('page_slug', None)
        url = kwargs.pop('url', None)

        # allow either fields as identifiers
        try:
            store = Store.objects.get(Q(id=store_id) | Q(slug=store_id))
        except (Store.DoesNotExist, MultipleObjectsReturned) as err:
            store = None
            if store_id:  # told to scrape a store, but no such store
                raise

        if page_slug:
            page = Page.objects.get(url_slug=page_slug)
            feed = page.feed
        else:
            page = feed = None

        urls_folder = kwargs.pop('folder', None)
        if urls_folder:
            print "--folder option is deprecated (not useful in any way)"
        else:
            urls_folder = join(dirname(dirname(dirname(__file__))), 'urls')

        if store:  # you said scrape this store; I will scrape this store
            stores = [store]
        else:  # scrape all stores
            stores = Store.objects.all()

        if store and url:
            run_scraper(url=url, store=store, page=page, feed=feed)

        print "This multiple-scraper trip contains the URLs:"
        for store in stores:
            print store.slug
            file_link = join(urls_folder, store.slug.lower() + '.json')  # ../gap.json
            configs = json.loads(read_a_file(file_link))
            for config in configs:
                print '- ' + config['url']

        for store in stores:
            file_link = join(urls_folder, store.slug.lower() + '.json')  # ../gap.json
            configs = json.loads(read_a_file(file_link))
            for config in configs:
                if not "store" in config:
                    config.update({"store": store})
                if not "page" in config:
                    config.update({"page": page})
                if not "feed" in config:
                    config.update({"feed": feed})
                run_scraper(**config)

def run_scraper(url,
                store=None, store_id=None, store_slug=None,
                page=None, page_id=None, page_slug=None,
                feed=None, feed_id=None):
    """Reads a config (as expanded args) and runs scrapers with similar
    instructions.

    Only required parameter: url (guess store, no auto-add-to-feed)
    """
    if not store and store_slug:
        store = Store.objects.get(slug=store_slug)

    if not store and store_id:
        store = Store.objects.get(id=store_id)
        
    if not (feed or page) and page_slug:
        page = Page.objects.get(url_slug=page_slug)
        feed = page.feed

    if not (feed or page) and page_id:
        page = Page.objects.get(id=page_id)
        feed = page.feed

    if not feed and feed_id:
        feed = Feed.objects.get(id=feed_id)

    if not page and feed:
        page = feed.pages.all()[0]

    # "scrape all urls for whichever store, or all stores if store is missing"

    scraper = CloudScraper()
    return scraper.subscrape(urls=[url], store=store, page=page, feed=feed)
