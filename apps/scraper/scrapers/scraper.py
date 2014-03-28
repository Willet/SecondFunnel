from apps.assets.models import Category

class ScraperException(Exception):
    pass

class Scraper(object):

    PRODUCT_DETAIL = 'product-detail'
    PRODUCT_CATEGORY = 'product-category'
    CONTENT_DETAIL = 'content-detail'
    CONTENT_CATEGORY = 'content-category'

    def __init__(self, store):
        self.store = store

    # the regex or list of regexs that match the url's that this scraper can scrape
    def get_regex(self, values={}):
        raise NotImplementedError

    # is passed the original url plus any values that are being passed to the scraper
    # return a string which is used as the new url
    def parse_url(self, url, values={}, **kwargs):
        return url

    # returns the type of scraper, types are defined as constants in the Scraper class
    def get_type(self, values={}):
        raise NotImplementedError

    def next_scraper(self, values={}):
        return None

    def _process_image(self, url):
        print(url)
        return url

    def _add_to_category(self, product, name=None, url=None):
        try:
            if url is None:
                category = Category.objects.get(store=self.store, name=name)
            else:
                category = Category.objects.get(store=self.store, url=url)
        except Category.DoesNotExist:
            if url is None:
                raise ScraperException('url must be provided if category does not exist')
            category = Category(store=self.store, name=name, url=url)
            category.save()
        category.products.add(product)

    # the actual scraper
    # for category scrapers, a store is also added to the arguments
    # for detail scrapers, a product or content object is added to the arguments
    def scrape(self, driver, url, values={}, **kwargs):
        raise NotImplementedError

    def validate(self, values={}, **kwargs):
        return True