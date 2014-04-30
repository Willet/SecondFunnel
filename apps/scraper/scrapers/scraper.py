import hashlib
import json
import re
from time import sleep
import urllib

from bs4 import BeautifulSoup
import bleach
from hammock import Hammock
from django.conf import settings

from apps.assets.models import Category, ProductImage, Product
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path
from apps.pinpoint.utils import read_remote_file
from apps.scraper.errors import ScraperException
from apps.scraper.scrapers import ALL_SCRAPERS
from apps.utils import chunks
from secondfunnel.errors import deprecated


class Scraper(object):
    """
    Base class for all scrapers

    The values variable is a dictionary that is passed around by the controller
    to all functions in the scraper and to all sub-scrapers, it can be added to
    by any function and is not changed by the controller

    To allow the scraper to be run without explicitly specifying when to run,
    the regexs variable must define a list of regexs for the scraper
    """
    store = None  # override for automatic store-product association.
    regexs = []

    def __init__(self, store=None):
        if store:
            self.store = store

    def parse_url(self, url, values, **kwargs):
        """Transform a url to one that we will actually scrape."""
        return url

    @classmethod
    def _wrap_regex(cls, regex, has_parameters=False, allow_parameters=True):
        """
        Makes creation of regexs easier, wraps with matching for https? at the beginning
        of the regex and parameters and #'s at the end of the regex
        """
        regex = r'^(?:https?://)?' + regex
        if allow_parameters:
            if has_parameters:
                regex += r'(?:&[^\?/]*)?'
            else:
                regex += r'(?:\?[^\?/]*)?'
        regex += r'(?:#.*)?$'
        return regex

    @staticmethod
    def _wrap_url(url, **params):
        """If the url isn't a phantomjscloud url, make it one, using params
        that you pass (optional).
        If the url is already a phantomjscloud url, do not make it one.
        """
        if settings.PHANTOMJSCLOUD_API_URL in url:
            return url

        defaults = {
            'timeout': '10000',
            'abortOnJavascriptErrors': 'false',
            'delayTime': '0',
            'isDebug': 'false',
            'postDomLoadedTimeout': '3000',
            'geolocation': 'us',
            'requestType': 'text',
            'outputAsJson': 'false',
        }
        if not params:
            params = defaults
        params['targetUrl'] = url

        return "{0}/single/browser/v1/{1}/?{2}".format(
            settings.PHANTOMJSCLOUD_API_URL,
            settings.PHANTOMJSCLOUD_API_KEY,
            urllib.urlencode(params))

    @staticmethod
    def _sanitize_html(html):
        allowed_tags = ['div', 'ul', 'li', 'p', ]
        allowed_attrs = {
            '*': [],
        }
        return bleach.clean(html, tags=allowed_tags,
                            attributes=allowed_attrs, strip=True)

    def _process_image(self):
        raise NotImplementedError

    @staticmethod
    def get_scraper(url):
        """Finds the scraper that handles the url, specified by each scraper's
        'regexes' constant.
        """

        for scraper in ALL_SCRAPERS():
            if any(re.match(regex, url) for regex in scraper.regexs):
                return scraper

        raise ScraperException('No scraper defined for url: {0}'.format(url))

    @staticmethod
    def get_store(scraper):
        """Assuming the scraper has a store, returns one."""
        return getattr(scraper, 'store', None)

    def scrape(self, url):
        """Makes the request to the URL with the given.

        Returns the page string and a beautifulsoup-wrapped object.

        Because of an oversight, all responses have the same status.
        """
        contents, _ = read_remote_file(url)
        return (url, 200, BeautifulSoup(contents), contents)

    def process(self, url, page, text='', status=200, **kwargs):
        """
        The method used to run the scraper

        page is a BeautifulSoup object.

        CollectionScraper.process must invoke their own DetailScraper.scrape
        for whichever details they find appropriate.
        """
        raise NotImplementedError


class CloudScraper(Scraper):
    """PhantomJSCloud adapter"""
    API_URL = "batch/browser/v1/{API_KEY}/".format(
        API_ROOT=settings.PHANTOMJSCLOUD_API_URL,
        API_KEY=settings.PHANTOMJSCLOUD_API_KEY)
    API = Hammock(settings.PHANTOMJSCLOUD_API_URL)

    def _get_page_request(self, url, other=None):
        """generates a 'page-request' object mentioned in the docs:
        https://phantomjscloud.com/site/docs.html#/advanced_batchRequest#advanced_batchRequest

        (adding a page request to the POST body adds the urls to the
        batch request list to scrape, must of the time.)

        (I also don't know what the point of requestId is.)
        """
        obj = {
            "targetUrl": url,
            "isDebug": True,
            "geolocation": "us",
            "requestType": "text",
            "outputAsJson": True,
            "loadImages": False,
            "timeout": 30000,
            "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/33.0.1750.152 Chrome/33.0.1750.152 Safari/537.36",
            "postDomLoadedTimeout": 5000,
            "scrollTo": 1000000,  # further down enough for inf scroll
            "requestId": hashlib.md5(url).hexdigest()[:6],  # just a random str
        }
        # inf scroll
        obj.update({
            "execScripts": [{
                "targetPageLoaded": "setInterval(function () { "
                                        "window.scrollTo(0,document.body.scrollHeight); "
                                    "}, 500);"
            }],
        })
        if other:
            obj.update(other)

        return obj

    def _get_batch_request(self, urls, other=None):
        """generates a 'batch-request' object menioned in the docs:
        https://phantomjscloud.com/site/docs.html#/advanced_batchRequest#advanced_batchRequest

        (using this as the POST body supposedly makes phantomjscloud scrape
        those urls.)
        """
        obj = {
            "hostMaxOpen": 10,
            "batchRequests": [self._get_page_request(url) for url in urls],
        }
        if other:
            obj.update(other)

        return obj

    def _get_batch_callback_response(self, url, page_count=1):
        """Given a callback url, GET it indefinitely.

        Returns a list of "page-response"s (url, status, html, text).

        (See "batch-callback-response" in the docs)
        """
        trips = 0
        page_responses = []

        while trips < (page_count * 20):  # say a page takes 20 seconds on average
            trips += 1
            if trips % 10 == 0:
                print "Retrieving pages: [{0}/200 seconds elapsed, {1}/{2} pages done]".format(
                    trips, len(page_responses), page_count)
            sleep(1)  # wait time in seconds; arbitrary number

            # call the callback url (note: calling the callback url will remove results)
            resp = Hammock(url).POST()
            resp_dct = resp.json()

            still_processing = resp_dct.get('stillProcessing')
            just_completed = resp_dct.get('justCompleted')  # list<str>

            if just_completed:
                just_completed = [self._get_page_response(j) for j in just_completed]
                # print "adding {0}".format(just_completed)
            page_responses.extend(just_completed)

            # no more pages to get from the cloud
            if not still_processing or still_processing in [0, '0', u'0']:
                break
        else:
            # that's (pages * 20) seconds and the cloud
            # still hasn't processed everything
            raise IOError("PhantomJSCloud timeout")

        # print "Processing complete: {0}".format(len(page_responses))
        return page_responses

    def _get_page_response(self, response_text):
        """Returns a tuple of (url, status, content, text).

        A response dict from the callback should look like this:
        {
            "request": { ... },
            "serviceMetadata": [ ... ],
            "execScriptsOutput": {},
            "resultUrl": "http://www.ohai.ca/",
            "pageResponseMetadata": {
                "contentType": "text/html; charset=utf-8",
                "headers": [
                    {
                        "name": "Server",
                        "value": "cloudflare-nginx"
                    }, ... ],
                "status": 200,
                "url": "http://www.ohai.ca/"
            },
            "frameData": {
                ...
                "content": "(data in frames)",
                "url": "http://www.ohai.ca/"
            },
            "pageContent": "<!DOCTYPE html><html ...>(your scraped page)</html>",
            "pageContentPlainText": "(just the text)",
            "totalTime": 692,
            "responseCategory": "OK"
        }
        """
        response_dct = json.loads(response_text)
        try:
            return (response_dct['request']['targetUrl'],
                    response_dct['pageResponseMetadata']['status'],
                    BeautifulSoup(response_dct['pageContent']),
                    response_dct['pageContentPlainText'])
        except KeyError as err:
            raise IOError("Malformed page-response object from phantomjscloud")

    def scrape(self, urls):
        """Accepts a list of urls. Returns page-response tuples.

        :param urls  either a list of strings, or a string (url)
        """
        if not isinstance(urls, list):
            urls = [urls]

        post_body = json.dumps(self._get_batch_request(urls=urls))

        resp = self.API(self.API_URL).POST(data=post_body,
            headers={'content-type': 'application/json'})

        # resp looks like {u'status': u'success',
        #               u'callbackUrl': u'http://api.phantomjscloud.com/...'}
        resp_dct = resp.json()
        if resp_dct.get('status') != 'success':
            raise IOError("phantomjscloud returned '{0}' instead of 'success'".format(
                resp_dct.get('status')))

        callback_url = resp_dct.get('callbackUrl')
        print "Scraping urls: %s" % urls
        # print "Querying callback url: {0}".format(callback_url)

        pages = self._get_batch_callback_response(callback_url,
                                                  page_count=len(urls))
        if len(pages) != len(urls):
            raise ValueError("phantomjscloud didn't give us the same number of pages?!")

        # pages be [(url, status, BeautifulSoup(contents), text), ...]
        return pages

    def subscrape(self, urls, page_scraper=None, store=None):
        """Scrape another set of pages based on current scraper's findings,
        then process the sub-pages using either a specific scraper, or
        the default scraper for a given url.
        """
        scraper = self.__class__()  # spawn self

        # break into batches of 10 max (lower this value if out of memory)
        for urls_chunk in chunks(urls, 10):
            pages = scraper.scrape(urls=urls_chunk)
            for url, status, page, text in pages:
                try:
                    if page_scraper:
                        pcrapper = page_scraper(store=store)
                    else:
                        pcrapper = scraper.get_scraper(url=url)(store=store)
                    pcrapper.process(url=url, page=page, text=text, status=status)
                    pcrapper = None
                except BaseException as err:
                    if settings.DEBUG:
                        raise
                    print "Failed to execute scraper for {0}: {1}".format(url, err)
                    continue  # this line is merely symbolic


class ProductScraper(CloudScraper):
    @staticmethod
    def get_product(url):
        """This is NOT Product.objects.get_or_create (allows blank,
        required fields)
        """
        try:
            product = Product.objects.filter(url=url)[0]
        except (Product.DoesNotExist, IndexError):
            product = Product(url=url)

        return product

    def _process_image(self, original_url, product):
        """
        This function uploads the image from the url and adds all necessary data to the image object

        If no image object is passed in, it creates a ProductImage as the default image object type
        """

        try:
            image = ProductImage.objects.get(original_url=original_url,
                                             product=product)
        except ProductImage.DoesNotExist:
            image = ProductImage(original_url=original_url, product=product)

        if not (image.url and image.file_type):
            print 'Processing image {0}'.format(original_url)
            data = process_image(original_url, create_image_path(self.store.id))
            image.url = data.get('url')
            image.file_type = data.get('format')
            image.dominant_color = data.get('dominant_colour')

            # save the image
            image.save()

            if product and not product.default_image:
                product.default_image = image
                product.save()
        else:
            print 'Image {0} has already been processed'.format(image)

        return image

    def _add_to_category(self, product, name=None, url=None):
        """
        This function will add the product to the category specified by
        the name and url passed in. Only one is  needed if the category
        exists. If the category does not exist, both name and url must
        be passed in so that the category can be created.
        """
        # strip html from name
        name = BeautifulSoup(name).get_text()

        if url is None and name is None:
            raise ScraperException('At least one of url or name must be provided to add to a category')

        if not name:
            name = ''
        
        name = name.lower()

        try:
            if name:
                category = Category.objects.get(store=self.store, name__iexact=name)
            else:
                category = Category.objects.get(store=self.store, url=url)
        except Category.DoesNotExist:
            # if the category does not exist, create it
            if not name:
                raise ScraperException('"name" must be provided if category does not exist')
            print "Creating category '{0}' for store {1}".format(name, self.store)
            category = Category(store=self.store, name=name)

        if url:
            category.url = url
        if name:
            category.name = name

        category.save()

        # add the product to the category
        print("Adding product {0} to category {1}".format(product, category))
        category.products.add(product)

        return category


class ProductCategoryScraper(ProductScraper):
    pass


class ProductDetailScraper(ProductScraper):
    pass


class ContentScraper(CloudScraper):
    def _process_image(self, source_url, image):
        """
        This function uploads the image from the url and adds all necessary data to the image object

        If no image object is passed in, it creates a ProductImage as the default image object type
        """

        if image.url and image.file_type and image.source_url:
            return image

        print 'Processing image {0}'.format(source_url)
        data = process_image(source_url, create_image_path(self.store.id))
        image.url = data.get('url')
        image.file_type = data.get('format')
        image.dominant_color = data.get('dominant_colour')
        image.source_url = source_url

        return image


class ContentCategoryScraper(ContentScraper):
    pass


class ContentDetailScraper(ContentScraper):
    pass
