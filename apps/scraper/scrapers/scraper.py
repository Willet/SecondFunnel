class Scraper(object):

    PRODUCT_DETAIL= 'product-detail'
    PRODUCT_CATEGORY = 'product-category'
    CONTENT_DETAIL = 'content-detail'
    CONTENT_CATEGORY = 'content-category'

    # the regex or list of regexs that match the url's that this scraper can scrape
    def get_regex(self):
        raise NotImplementedError

    # is passed the original url plus any values that are being passed to the scraper
    # can return a string which is used as the new url
    # or can return a dict where the new url is retrieved with the value 'url'
    # the dict is then added to the values being passed around and is passed to the scraper
    # plus all sub scrapers
    def parse_url(self, url, **kwargs):
        return url

    # returns the type of scraper, types are defined as constants in the Scraper class
    def get_type(self):
        raise NotImplementedError

    # the actual scraper
    # for category scrapers, a store is also added to the arguments
    # for detail scrapers, a product or content object is added to the arguments
    def scrape(self, driver, **kwargs):
        raise NotImplementedError