import sys, re
from selenium import webdriver

from apps.assets.models import Product, Store
from apps.scraper.scrapers.gap.gap_product_scraper_selenium import scrape_product_page, scrape_category_page

def get_gap_product_url(url):
    id_regex = r'^(?:https?://)?(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=(\d{6})\d*(?:&.*)?$'
    result = re.match(id_regex, url)
    sku = result.group(1)
    url = 'http://www.gap.com/browse/product.do?pid=' + sku
    return url

scrapers = [(scrape_product_page, 'detail', r'^(?:https?://)?(?:www\.)?gap\.com/browse/product\.do\?[^/\?]*pid=\d{6,}(?:&.*)?$', get_gap_product_url),
            (scrape_category_page, 'category', r'^(?:https?://)?(?:www\.)?gap\.com/browse/category\.do\?[^/\?]*cid=\d{6,}(?:&.*)?$', None),]

def run_scraper(store, url):
    try:
        # "http://www.gap.com/browse/product.do?pid=941851"
        for fun, type, regex, get_url in scrapers:
            if re.match(regex, url):
                if get_url:
                    url = get_url(url)
                print type
                print url
                break
        else:
            return
        driver = webdriver.PhantomJS()
        driver.get(url)
        if type == 'detail':
            try:
                product, _ = Product.objects.get(store=store, url=url)
            except Product.DoesNotExist:
                product = Product(store=store, url=url)
            product = fun(product, driver)
            print product.to_json()
        elif type == 'category':
            for product in fun(store, driver):
                #product.save()
                run_scraper(store, product.url)
    except Exception as e:
        print e
    finally:
        if driver:
            driver.close()


store_id = sys.argv[1]
url = sys.argv[2]
store = Store.objects.get(old_id=store_id)
run_scraper(store, url)