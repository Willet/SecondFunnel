import os
import re
import traceback

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from selenium.common.exceptions import WebDriverException

from apps.assets.models import Product, Store
from apps.scraper.scrapers import ProductDetailScraper
from apps.scraper.scrapers import GapProductScraper, GapCategoryScraper
from apps.scraper.scrapers import MadewellProductScraper, MadewellCategoryScraper, MadewellMultiProductScraper
from apps.scraper.scrapers import VoyagePriveCategoryScraper
from apps.scraper.scrapers import PinterestPinScraper, PinterestAlbumScraper
from apps.scraper.scrapers import StyldByFilterScraper, StyldByPartnersScraper


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option('--store-id', default=None, dest='store-id'),
                                             make_option('--url', default=None),
                                             make_option('--folder', default=None))

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
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
        ]

    def handle(self, *args, **kwargs):
        store_id = kwargs.pop('store-id', None)
        url = kwargs.pop('url', None)
        folder = kwargs.pop('folder', None)
        if url:
            if not store_id:
                raise CommandError('store-id must be specified if url is included')
            store = Store.objects.get(id=store_id)
            self.set_store(store)
            self.run_scraper(url=url)
        else:
            if not folder:
                folder = ''
                for item in os.path.abspath(__file__).split('/')[:-3]:
                    folder += item + '/'
                folder += 'urls'
            for file_name in os.listdir(folder):
                if not folder.endswith('/'):
                    folder += '/'
                url_file = open(folder + file_name)
                store_slug = file_name.split('.')[0]
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

        return None

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

            for dictionary in scraper.scrape(url=url, product=product, content=content, values=values):
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
            if scraper and scraper.driver:
                scraper.driver.close()
