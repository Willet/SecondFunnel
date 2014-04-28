import re
import traceback

from os import listdir
from os.path import join, dirname

from optparse import make_option
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from selenium.common.exceptions import WebDriverException

from apps.assets.models import Product, Store
from apps.scraper.errors import ScraperException
from apps.scraper.models import ProductDetailScraper, CloudScraper

from apps.scraper.scrapers.gap import GapProductScraper, GapCategoryScraper, STLScraper
from apps.scraper.scrapers.madewell import MadewellProductScraper, MadewellCategoryScraper, MadewellMultiProductScraper
from apps.scraper.scrapers.voyage_prive import VoyagePriveCategoryScraper
from apps.scraper.scrapers.pinterest import PinterestPinScraper, PinterestAlbumScraper
from apps.scraper.scrapers.styldby import StyldByFilterScraper, StyldByPartnersScraper


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--store-id', default=None, dest='store-id'),
        make_option('--url', default=None),
        make_option('--folder', default=None))  # --folder is deprecated

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__()
        self.scrapers = [
            GapProductScraper,
            GapCategoryScraper,
            MadewellProductScraper,
            MadewellCategoryScraper,
            MadewellMultiProductScraper,
            VoyagePriveCategoryScraper,
            PinterestPinScraper,
            PinterestAlbumScraper,
            StyldByFilterScraper,
            StyldByPartnersScraper,
            STLScraper,
        ]

    def handle(self, *args, **kwargs):
        """
        If called with store-id (somehow) and url, scrapes that url for
            that store.
        Otherwise, scrapes all urls listed in all text files in the urls folder.
        """
        store_id = kwargs.pop('store-id', None)
        url = kwargs.pop('url', None)
        urls_folder = kwargs.pop('folder', None)

        # allow either fields as identifiers
        try:
            store = Store.objects.get(Q(id=store_id) | Q(slug=store_id))
        except (Store.DoesNotExist, MultipleObjectsReturned) as err:
            store = None
            if store_id:  # told to scrape a store, but no such store
                raise

        # "scrape all urls for whichever store, or all stores if store is missing"
        if urls_folder:
            print "--folder option is deprecated (not useful in any way)"
        else:
            urls_folder = join(dirname(dirname(dirname(__file__))), 'urls')

        if store:  # you said scrape this store; I will scrape this store
            stores = [store]
        else:  # scrape all stores
            stores = Store.objects.all()

        urls = []
        if url:
            urls = [url]
        else:
            # scraper itinerary
            print "This multiple-scraper trip contains the URLs:"
            for store in stores:
                print store.slug
                file_name = store.slug.lower() + '.txt'
                file_link = join(urls_folder, file_name)
                try:
                    with open(file_link) as url_file:
                        for line in url_file:
                            # support comments
                            if line.startswith('#'):
                                print "Skipping {0}".format(line[1:])
                                continue
                            line = line.replace('\n', '')
                            print "- {0}".format(line)
                            urls.append(line)
                except IOError:
                    pass

        scraper = CloudScraper()
        pages = scraper.scrape(urls=urls)

        for url, status, page, text in pages:
            try:
                page_scraper = scraper.get_scraper(url=url)
                page_scraper.process(url=url, status=status, page=page, text=text)
            except BaseException as err:
                print "Oh no! Something bad happened: {0}".format(err)
                continue  # this line is merely symbolic

    def set_store(self, store):
        self.store = store

    def get_scraper(self, url):
        """Finds the scraper that handles the url, specified by each scraper's
        'regexes' constant.
        """

        for scraper in self.scrapers:
            if any(re.match(regex, url) for regex in scraper.regexs):
                return scraper

        raise ScraperException('No scraper defined for url: {0}'.format(url))
