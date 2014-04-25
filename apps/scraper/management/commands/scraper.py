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
from apps.scraper.scrapers import ProductDetailScraper
from apps.scraper.scrapers import GapProductScraper, GapCategoryScraper
from apps.scraper.scrapers import MadewellProductScraper, MadewellCategoryScraper, MadewellMultiProductScraper
from apps.scraper.scrapers import VoyagePriveCategoryScraper
from apps.scraper.scrapers import PinterestPinScraper, PinterestAlbumScraper
from apps.scraper.scrapers import StyldByFilterScraper, StyldByPartnersScraper
from apps.scraper.scrapers import STLScraper
from apps.scraper.scrapers.scraper import ScraperException


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

        if store and url:
            # "scrape this url for this store"
            self.set_store(store)
            return self.run_scraper(url=url)

        # scraper itinerary
        print "This multiple-scraper trip contains the URLs:"
        for store in stores:
            print store.slug
            file_name = store.slug.lower() + '.txt'
            file_link = join(urls_folder, file_name)
            try:
                with open(file_link) as url_file:
                    for line in url_file:
                        print "- {0}".format(line.replace('\n', ''))
            except IOError:
                pass

        for store in stores:
            try:
                self.set_store(store)
                file_name = store.slug.lower() + '.txt'
                file_link = join(urls_folder, file_name)
                print('retrieving url from "{0}"'.format(file_link))
                with open(file_link) as url_file:
                    for line in url_file:
                        self.run_scraper(url=line)
            except BaseException as err:
                print "Oh no! Something bad happened: {0}".format(err)
                continue  # this line is merely symbolic

    def set_store(self, store):
        self.store = store

    def get_scraper(self, url):
        """
        If a scraper exists with a regex that matches the given url, then
        that scraper is returned, else None is returned
        """
        for scraper in self.scrapers:
            regexs = scraper.regexs
            if any(re.match(regex, url) for regex in regexs):
                return scraper

        raise ScraperException('No scraper defined for given url')

    def run_scraper(self, url, product=None, content=None, scraper=None, values=None):
        if values is None:
            values = {}
        # strip outer spaces from the url
        url = url.strip()
        try:
            if scraper is None:
                scraper = self.get_scraper(url)(self.store)

            # if no scraper has been found, exit
            if scraper is None:
                print('no scraper found for url - ' + url)
                return

            # retrieve the url for the driver to load
            url = scraper.parse_url(url=url, values=values)

            if isinstance(scraper, ProductDetailScraper):
                if not product:
                    try:
                        product = Product.objects.get(store=self.store, url=url)
                    except Product.DoesNotExist:
                        product = Product(store=self.store, url=url)

            # loops through all returned dictionaries for the scraper
            # if a url is returned, run_scraper() is called with the arguments in the returned dictionary
            # if no url is returned, the content or product model is printed out
            # if no content or product is returned, an error is printed
            for dictionary in scraper.scrape(url=url, product=product,
                                             content=content, values=values):
                if dictionary.get('url', None):
                    scraper_vars = {}
                    scraper_vars.update(dictionary)
                    scraper_vars.update({'values': values.copy()})
                    self.run_scraper(**scraper_vars)
                elif dictionary.get('content', None):
                    print('\n' + str(dictionary.get('content').to_json()))
                elif dictionary.get('product', None):
                    print('\n' + str(dictionary.get('product').to_json()))
                else:
                    print('bad scraper return, must return either a url or a model for a product or content')

        except WebDriverException:
            print('There was a problem with the webdriver')
            traceback.print_exc()

        except BaseException:
            # catches all exceptions so that if one detail scraper were to have an error
            # any content scraper that may have called it would keep working
            print('There was a problem while scraping ' + url)
            traceback.print_exc()
        finally:
            # make sure to close the driver if it exists
            if scraper and hasattr(scraper, 'driver'):
                scraper.driver.close()
