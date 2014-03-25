class Scraper(object):

    PRODUCT_DETAIL= 'product-detail'
    PRODUCT_CATEGORY = 'product-category'
    CONTENT_DETAIL = 'content-detail'
    CONTENT_CATEGORY = 'content-category'

    # the regex or list of regexs that match the url's that this scraper can scrape
    def get_regex(self):
        raise NotImplementedError

    # returns the cleaned up url from an input url, the returned url is the url
    # that is loaded and also the one that creates products or content for
    # detail scrapers
    def get_url(self, url):
        return url

    # returns the type of scraper, types are defined as constants in the Scraper class
    def get_type(self):
        raise NotImplementedError

    # the actual scraper
    # for category scrapers, a store is also added to the arguments
    # for detail scrapers, a product or content object is added to the arguments
    def scrape(self, driver, **kwargs):
        raise NotImplementedError