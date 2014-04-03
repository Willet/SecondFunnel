import sys
import re
import traceback
import argparse

from selenium import webdriver

from apps.assets.models import Product, Store, Video
from apps.scraper.scrapers.scraper import ProductDetailScraper, ProductCategoryScraper, ContentDetailScraper, \
    ContentCategoryScraper
from apps.scraper.scrapers.gap.gap_product_scrapers import GapProductScraper, GapCategoryScraper
from apps.scraper.scrapers.madewell.madewell_product_scrapers import MadewellProductScraper, MadewellCategoryScraper, \
    MadewellMultiProductScraper
from apps.scraper.scrapers.content.pinterest_scraper import PinterestPinScraper, PinterestAlbumScraper
from apps.scraper.scrapers.gap.styldby_scraper import StyldByFilterScraper


class Controller(object):
    def __init__(self, store):
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

            # initialize the head-less browser PhantomJS
            print('loading url - ' + url)
            # hmm... might not run on windows
            driver = webdriver.PhantomJS(service_log_path='/tmp/ghostdriver.log')
            driver.get(url)

            if isinstance(scraper, ProductDetailScraper):
                # find or make a new product
                # Product.objects.find_or_create not used as we do not want to save right now
                if not product:
                    try:
                        product = Product.objects.get(store=self.store, url=url)
                    except Product.DoesNotExist:
                        product = Product(store=self.store, url=url)
                for product in scraper.scrape(driver=driver, url=url, product=product, values=values):
                    print(product.to_json())
                    break
            elif isinstance(scraper, ProductCategoryScraper):
                for product in scraper.scrape(driver=driver, url=url, values=values):
                    next_scraper = scraper.next_scraper(values=values)
                    self.run_scraper(url=product.url, product=product, values=values.copy(), scraper=next_scraper)
            elif isinstance(scraper, ContentDetailScraper):
                # there is no way to retrieve content from loaded url as the url
                # variable in content is not consistent
                for content in scraper.scrape(driver=driver, url=url, content=content, values=values):
                    content.save()
                    print(content.to_json())
                    break
            elif isinstance(scraper, ContentCategoryScraper):
                for content in scraper.scrape(driver=driver, url=url, values=values):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='run a scraper.')
    parser.add_argument('store_id', type=int, help='the id for the store for the scraper')
    parser.add_argument('url', help='the url to scrape')

    args, unknown = parser.parse_known_args()

    controller = Controller(Store.objects.get(id=args.store_id))

    controller.run_scraper(args.url)
