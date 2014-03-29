import sys
import re
import traceback

from selenium import webdriver

from apps.assets.models import Product, Store, Content
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

            url = scraper.parse_url(url=url, values=values)

            # initialize the head-less browser PhantomJS
            #print('loading url - ' + url)
            driver = webdriver.PhantomJS()
            driver.get(url)
            #print('loaded')

            scraper_type = scraper.get_type(values=values)

            if scraper_type == Scraper.PRODUCT_DETAIL:
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
                content = scraper.scrape(driver=driver, url=url, content=content, values=values)
                print(content.to_json())
                if not self.dry_run and scraper.validate(content=content, values=values):
                    content.save()
            elif scraper_type == Scraper.CONTENT_CATEGORY:
                for content, content_url in scraper.scrape(driver=driver, url=url, values=values):
                    if scraper.validate(content=content, values=values):
                        next_scraper = scraper.next_scraper(values=values)
                        self.run_scraper(url=content_url, content=content, values=values.copy(), scraper=next_scraper)

        except Exception:
            print('There was a problem while scraping ' + url)
            traceback.print_exc()
        finally:
            if driver:
                driver.close()


start_store_id = sys.argv[1]
start_url = sys.argv[2]
start_store = Store.objects.get(id=start_store_id)

controller = Controller(start_store)

controller.run_scraper(start_url)