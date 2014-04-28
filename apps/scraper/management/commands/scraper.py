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
                page_scraper = scraper.get_scraper(url=url).parse(url=url)
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

    def run_scraper(self, url, product=None, content=None, scraper=None, values=None):
        if values is None:
            values = {}
        # strip outer spaces from the url
        url = url.strip()
        try:
            try:
                scraper = scraper or self.get_scraper(url)(self.store)
            except ScraperException:
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
            for dictionary in scraper.parse(url=url, product=product,
                                            content=content, values=values):
                if dictionary.get('url', None):
                    scraper_vars = {}
                    scraper_vars.update(dictionary)
                    scraper_vars.update({'values': values.copy()})
                    self.run_scraper(**scraper_vars)
                elif dictionary.get('content', None):
                    print 'Content attributes: {0}'.format(dictionary['content'].to_json())
                elif dictionary.get('product', None):
                    print 'Product attributes: {0}'.format(dictionary['product'].to_json())
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
