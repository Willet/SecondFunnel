import os
import re
import traceback

from optparse import make_option
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

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
    option_list = BaseCommand.option_list + (make_option('--store-id', default=None, dest='store-id'),
                                             make_option('--url', default=None),
                                             make_option('--folder', default=None))

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
        If called with folder,
        Otherwise, scrapes all urls listed in all text files in the urls folder.
        """
        store = None
        store_id = kwargs.pop('store-id', None)
        url = kwargs.pop('url', None)
        folder = kwargs.pop('folder', None)
        if url:
            try:
                store = Store.objects.get(id=store_id)
            except ObjectDoesNotExist:
                pass
            try:
                if not store:
                    store = Store.objects.get(slug=store_id)  # identifier was a slug
            except ObjectDoesNotExist:
                raise CommandError('store-id must be specified if url is included')

            self.set_store(store)
            self.run_scraper(url=url)
        else:
            if not folder:
                # e.g. /home/brian/Envs/SecondFunnel/apps/scraper/urls
                folder = os.path.join(os.path.dirname(os.path.dirname(
                    os.path.dirname(__file__))), 'urls') + '/'
            for file_name in os.listdir(folder):
                print('retrieving url from "{0}"'.format(
                    os.path.join(folder,file_name)))
                url_file = open(os.path.join(folder,file_name))
                store_slug = file_name.split('.')[0]  # 'gap' from 'gap.txt'
                try:
                    store = Store.objects.get(slug=store_slug)
                    self.set_store(store)
                    for line in url_file:
                        self.run_scraper(url=line)
                except Store.DoesNotExist:
                    print('store %s does not exist' % store_slug)

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
