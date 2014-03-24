class Scraper(object):

    PRODUCT_DETAIL= 'product-detail'
    PRODUCT_CATEGORY = 'product-category'
    CONTENT_DETAIL = 'content-detail'
    CONTENT_CATEGORY = 'content-category'

    def get_regex(self):
        raise NotImplementedError

    def get_url(self, url):
        return url

    def get_type(self):
        raise NotImplementedError

    def scrape(self, driver, **kwargs):
        raise NotImplementedError