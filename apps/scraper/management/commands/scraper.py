import os
import re
import traceback

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from apps.assets.models import Product, Store, Video
from apps.scraper.scrapers.scraper import ProductDetailScraper, ProductCategoryScraper, ContentDetailScraper, \
    ContentCategoryScraper
from apps.scraper.scrapers.gap.gap_product_scrapers import GapProductScraper, GapCategoryScraper
from apps.scraper.scrapers.madewell.madewell_product_scrapers import MadewellProductScraper, MadewellCategoryScraper, \
    MadewellMultiProductScraper
from apps.scraper.scrapers.content.pinterest_scraper import PinterestPinScraper, PinterestAlbumScraper
from apps.scraper.scrapers.gap.styldby_scraper import StyldByFilterScraper, StyldByPartnersScraper


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option('--store-id', default=None, dest='store-id'),
                                             make_option('--url', default=None),
                                             make_option('--folder', default=None))

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
        self.scrapers = [
            GapProductScraper(store),
            GapCategoryScraper(store),
            MadewellProductScraper(store),
            MadewellCategoryScraper(store),
            MadewellMultiProductScraper(store),
            PinterestPinScraper(store),
            PinterestAlbumScraper(store),
            StyldByFilterScraper(store),
            StyldByPartnersScraper(store),
        ]

    def get_scraper(self, url, values=None):
        """
        If a scraper exists with a regex that matches the given url, then
        that scraper is returned, else None is returned
        """
        if values is None:
            values = {}

        for scraper in self.scrapers:
            regexs = scraper.get_regex(values=values)
            if any(re.match(regex, url) for regex in regexs):
                return scraper

        return None

    def run_scraper(self, url, product=None, content=None, scraper=None, values=None):
        if values is None:
            values = {}
        # strip outer spaces from the url
        url = url.strip()
        driver = None
        try:
            if scraper is None:
                scraper = self.get_scraper(url, values)

            # if no scraper has been found, exit
            if scraper is None:
                print('no scraper found for url - ' + url)
                return

            # retrieve the url for the driver to load
            url = scraper.parse_url(url=url, values=values)

            if isinstance(scraper, ProductDetailScraper):
                # find or make a new product
                # Product.objects.find_or_create not used as we do not want to save right now
                if not product:
                    try:
                        product = Product.objects.get(store=self.store, url=url)
                    except Product.DoesNotExist:
                        product = Product(store=self.store, url=url)
                for product in scraper.scrape(url=url, product=product, values=values):
                    print('\n' + str(product.to_json()))
                    break
            elif isinstance(scraper, ProductCategoryScraper):
                for product in scraper.scrape(url=url, values=values):
                    next_scraper = scraper.next_scraper(values=values)
                    self.run_scraper(url=product.url, product=product, values=values.copy(), scraper=next_scraper)
            elif isinstance(scraper, ContentDetailScraper):
                # there is no way to retrieve content from loaded url as the url
                # variable in content is not consistent
                for content in scraper.scrape(url=url, content=content, values=values):
                    content.save()
                    print('\n' + str(content.to_json()))
                    break
            elif isinstance(scraper, ContentCategoryScraper):
                for content in scraper.scrape(url=url, values=values):
                    if not scraper.has_next_scraper(values=values):
                        print(content.to_json())
                        continue
                    next_scraper = scraper.next_scraper(values=values)
                    if isinstance(content, Video):
                        self.run_scraper(url=content.url, content=content, values=values.copy(), scraper=next_scraper)
                    else:
                        self.run_scraper(url=content.original_url, content=content, values=values.copy(),
                                         scraper=next_scraper)

        except BaseException:
            # catches all exceptions so that if one detail scraper were to have an error
            # any content scraper that may have called it would keep working
            print('There was a problem while scraping ' + url)
            traceback.print_exc()
        finally:
            # make sure to close the driver if it exists
            if driver:
                driver.close()
