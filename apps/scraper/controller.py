import sys
import re

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from apps.assets.models import Product, Store, Feed, Page, Tile
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


def run_scraper(store, url):
    driver = None
    try:
        # "http://www.gap.com/browse/product.do?pid=941851"

        # checking if any scraper has the correct regex to scrape the given url
        for scraper in scrapers:
            if isinstance(scraper.get_regex(), list):
                if any(re.match(regex, url) for regex in scraper.get_regex()):
                    url = scraper.get_url(url)
                    break

            elif re.match(scraper.get_regex(), url):
                url = scraper.get_url(url)
                break
        # if no scraper has been found, exit
        else:
            print('no scraper found')
            return

        # initialize the head-less browser PhantomJS
        driver = webdriver.PhantomJS()
        driver.get(url)

        if scraper.get_type() == Scraper.PRODUCT_DETAIL:
            try:
                product = Product.objects.get(store=store, url=url)
            except Product.DoesNotExist:
                product = Product(store=store, url=url)
            product = scraper.scrape(driver, product=product)
            print product.to_json()
            product.save()
        elif scraper.get_type() == Scraper.PRODUCT_CATEGORY:
            for url in scraper.scrape(driver, store=store):
                run_scraper(store, url)

    finally:
        if driver:
            driver.close()


start_store_id = sys.argv[1]
start_url = sys.argv[2]
start_store = Store.objects.get(old_id=start_store_id)
run_scraper(start_store, start_url)