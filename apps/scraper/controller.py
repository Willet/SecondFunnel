import sys
import re

from selenium import webdriver

from apps.assets.models import Product, Store
from apps.scraper.scrapers.scraper import Scraper
from apps.scraper.scrapers.gap.gap_product_scrapers import GapProductScraper, GapCategoryScraper
from apps.scraper.scrapers.madewell.madewell_product_scrapers import MadewellProductScraper, MadewellCategoryScraper

# define all the possible scrapers
scrapers = [
    GapProductScraper(),
    GapCategoryScraper(),
    MadewellProductScraper(),
    MadewellCategoryScraper(),
]


def run_scraper(store, url, product=None, values={}):
    driver = None
    try:
        # "http://www.gap.com/browse/product.do?pid=941851"

        # checking if any scraper has the correct regex to scrape the given url
        for scraper in scrapers:
            if isinstance(scraper.get_regex(), list):
                if any(re.match(regex, url) for regex in scraper.get_regex()):
                    url_return = scraper.parse_url(url, **values)
                    break

            elif re.match(scraper.get_regex(), url):
                url_return = scraper.parse_url(url, **values)
                break
        # if no scraper has been found, exit
        else:
            logging.error('no scraper found for url ' + url)
            return

        if isinstance(url_return, dict):
            url = url_return.pop('url', url)
            values.update(url_return)
        else:
            url = url_return or url

        # initialize the head-less browser PhantomJS
        print('loading url - ' + url)
        driver = webdriver.PhantomJS()
        driver.get(url)

        if scraper.get_type() == Scraper.PRODUCT_DETAIL:
            if product is None:
                try:
                    product = Product.objects.get(store=store, url=url)
                except Product.DoesNotExist:
                    product = Product(store=store, url=url)
            product = scraper.scrape(driver, product=product, **values)
            print(product.to_json())
            #validate(product)
            #product.save()
        elif scraper.get_type() == Scraper.PRODUCT_CATEGORY:
            for product in scraper.scrape(driver, store=store, **values):
                run_scraper(store, product.url, product, values=values.copy())

    except BaseException:
        print('There was a problem in the scraper')
    finally:
        if driver:
            driver.close()


start_store_id = sys.argv[1]
start_url = sys.argv[2]
start_store = Store.objects.get(old_id=start_store_id)
run_scraper(start_store, start_url)