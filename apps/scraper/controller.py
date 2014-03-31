import sys
import re
import traceback
import argparse

from selenium import webdriver

from apps.assets.models import Product, Store
from apps.scraper.scrapers.scraper import Scraper
from apps.scraper.scrapers.gap.gap_product_scrapers import GapProductScraper, GapCategoryScraper
from apps.scraper.scrapers.madewell.madewell_product_scrapers import MadewellProductScraper, MadewellCategoryScraper
from apps.scraper.scrapers.content.pinterest_scraper import PinterestPinScraper, PinterestAlbumScraper


class Controller(object):
    def __init__(self, store, dry_run=False):
        self.dry_run = dry_run
        self.store = store
        self.scrapers = [
            GapProductScraper(store, dry_run),
            GapCategoryScraper(store, dry_run),
            MadewellProductScraper(store, dry_run),
            MadewellCategoryScraper(store, dry_run),
            PinterestPinScraper(store, dry_run),
            PinterestAlbumScraper(store, dry_run),
        ]

    def run_scraper(self, url, product=None, content=None, scraper=None, values={}):
        # strip outer spaces from the url
        url = url.strip()
        driver = None
        try:
            if scraper is None:
                # checking if any scraper has the correct regex to scrape the given url
                for temp_scraper in self.scrapers:
                    scraper_regex = temp_scraper.get_regex(values=values)
                    if isinstance(scraper_regex, list):
                        if any(re.match(regex, url) for regex in scraper_regex):
                            scraper = temp_scraper
                            break

                    elif re.match(scraper_regex, url):
                        scraper = temp_scraper
                        break
            # if no scraper has been found, exit
            if scraper is None:
                print('no scraper found for url - ' + url)
                return

            # retrieve the url for the driver to load
            url = scraper.parse_url(url=url, values=values)

            # initialize the head-less browser PhantomJS
            driver = webdriver.PhantomJS()
            driver.get(url)

            # get tye type of scraper
            scraper_type = scraper.get_type(values=values)

            if scraper_type == Scraper.PRODUCT_DETAIL:
                # find or make a new product
                # Product.objects.find_or_create not used as we do not want to save right now
                if product is None:
                    try:
                        product = Product.objects.get(store=self.store, url=url)
                    except Product.DoesNotExist:
                        product = Product(store=self.store, url=url)
                product = scraper.scrape(driver=driver, url=url, product=product, values=values)
                print(product.to_json())
                if not self.dry_run and scraper.validate(product=product, values=values):
                    product.save()
            elif scraper_type == Scraper.PRODUCT_CATEGORY:
                for product in scraper.scrape(driver=driver, url=url, values=values):
                    if scraper.validate(product=product, values=values):
                        next_scraper = scraper.next_scraper(values=values)
                        self.run_scraper(url=product.url, product=product, values=values.copy(), scraper=next_scraper)
            elif scraper_type == Scraper.CONTENT_DETAIL:
                # there is no way to retrieve content from loaded url as the url
                # variable in content is not consistent
                content = scraper.scrape(driver=driver, url=url, content=content, values=values)
                print(content.to_json())
                if not self.dry_run and scraper.validate(content=content, values=values):
                    content.save()
            elif scraper_type == Scraper.CONTENT_CATEGORY:
                for content, content_url in scraper.scrape(driver=driver, url=url, values=values):
                    if scraper.validate(content=content, values=values):
                        next_scraper = scraper.next_scraper(values=values)
                        self.run_scraper(url=content_url, content=content, values=values.copy(), scraper=next_scraper)

        except BaseException:
            # catches all exceptions so that if one detail scraper were to have an error
            # any content scraper that may have called it would keep working
            print('There was a problem while scraping ' + url)
            traceback.print_exc()
        finally:
            # make sure to close the driver if it exists
            if driver:
                driver.close()


parser = argparse.ArgumentParser(description='run a scraper.')
parser.add_argument('store_id', type=int, help='the id for the store for the scraper')
parser.add_argument('url', help='the url to scrape')
parser.add_argument('--dryrun', default=False, action='store_true', help='test the scraper without saving anything')

args, unknown = parser.parse_known_args()

controller = Controller(Store.objects.get(id=args.store_id), args.dryrun)

controller.run_scraper(args.url)