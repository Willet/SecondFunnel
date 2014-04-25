import hashlib
import json
from time import sleep
import urllib
from bs4 import BeautifulSoup
from django.db.models import Q
import bleach
from hammock import Hammock

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import DesiredCapabilities

from apps.assets.models import Category, ProductImage, Product
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path
from apps.pinpoint.utils import read_remote_file
from apps.scraper.errors import ScraperException
from django.conf import settings


class Scraper(object):
    """
    Base class for all scrapers

    The values variable is a dictionary that is passed around by the controller
    to all functions in the scraper and to all sub-scrapers, it can be added to
    by any function and is not changed by the controller

    To allow the scraper to be run without explicitly specifying when to run,
    the regexs variable must define a list of regexs for the scraper
    """
    regexs = []

    def __init__(self, store):
        # initialize the head-less browser PhantomJS
        # hmm... might not run on windows

        # try to initialize phantomJS twice before throwing an exception
        # (driver is not used for phantomjscloud ops
        attempts = 2
        while attempts:
            try:
                self.driver = webdriver.PhantomJS(service_log_path='/tmp/ghostdriver.log')
            except WebDriverException as err:
                attempts = attempts - 1
                if not attempts:
                    raise err
            else:
                break
        self.store = store

    def parse_url(self, url, values, **kwargs):
        """
        Optional method
        Returns a condensed url from the passed in url
        """
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

    @classmethod
    def _wrap_url(cls, url, **params):
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

    def scrape(self, url):
        """Makes the request to the URL with the given.

        Returns the page string and a beautifulsoup-wrapped object.

        There is no scrapy equivalent for this method.
        """
        contents, _ = read_remote_file(url)
        return contents, BeautifulSoup(contents)

    def _sanitize_html(cls, html):
        allowed_tags = ['div', 'ul', 'li', 'p', ]
        allowed_attrs = {
            '*': [],
        }
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)

    def parse(self, url, values, **kwargs):
        """
        The method used to run the scraper

        yield is used to return dictionaries with the required variables
        url must be included in the dictionary if another scraper must be run after this one
        product or content must be included if no scraper should be run after this one
        scraper can be included to explicitly define the next scraper
        """
        raise NotImplementedError


class CloudScraper(object):
    """PhantomJSCloud adapter"""
    API_ROOT = "http://api.phantomjscloud.com"  # move this when value used elsewhere
    API_KEY = "7707cc4bae3ee4d768d0d6f6b5e6856a58b530bd"
    API_URL = "batch/browser/v1/{API_KEY}/".format(API_ROOT=API_ROOT,
                                                   API_KEY=API_KEY)
    API = Hammock(API_ROOT)

    def get_page_request(self, url, other=None):
        """generates a 'page-request' object mentioned in the docs:
        https://phantomjscloud.com/site/docs.html#/advanced_batchRequest#advanced_batchRequest

        (adding a page request to the POST body adds the urls to the
        batch request list to scrape, must of the time.)

        (I also don't know what the point of requestId is.)
        """
        obj = {
            "targetUrl": url,
            "requestType": "text",
            "outputAsJson": True,
            "loadImages": False,
            "timeout": 30000,
            "postDomLoadedTimeout": 5000,
            "execScripts": [{
                "targetPageLoaded": "setInterval(function () { "
                                        "window.scrollTo(0,document.body.scrollHeight); "
                                    "}, 500);"
            }],
            "requestId": hashlib.md5(url).hexdigest()[:6],  # just a random str
        }
        if other:
            obj.update(other)

        return obj

    def get_batch_request(self, urls, other=None):
        """generates a 'batch-request' object menioned in the docs:
        https://phantomjscloud.com/site/docs.html#/advanced_batchRequest#advanced_batchRequest

        (using this as the POST body supposedly makes phantomjscloud scrape
        those urls.)
        """
        obj = {
            "hostMaxOpen": 10,
            "batchRequests": [self.get_page_request(url) for url in urls],
        }
        if other:
            obj.update(other)

        return obj

    def get_batch_callback_response(self, url):
        """Given a callback url, GET it indefinitely.

        Returns a list of "page-response"s (url, status, html, text).

        (See "batch-callback-response" in the docs)
        """
        trips = 0
        page_responses = []

        while True:
            trips = trips + 1
            print "Retrieving pages: [{0}/100]".format(trips)
            sleep(3)  # wait time in seconds; arbitrary number

            # call the callback url (note: calling the callback url will remove results)
            resp = Hammock(url).POST()
            resp_dct = resp.json()

            still_processing = resp_dct.get('stillProcessing')
            just_completed = resp_dct.get('justCompleted')  # list<str>

            if just_completed:
                just_completed = [self.get_page_response(j) for j in just_completed]
                print "adding {0}".format(just_completed)
            page_responses.extend(just_completed)

            # no more pages to get from the cloud
            if not still_processing or still_processing in [0, '0', u'0']:
                break

            if trips > 100:  # that's 5 minutes and the cloud
                             # still hasn't processed everything
                raise IOError("PhantomJSCloud timeout")

        print "processing complete: {0}".format(page_responses)
        return page_responses

    def get_page_response(self, response_text):
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
            return (response_dct['resultUrl'],
                    response_dct['pageResponseMetadata']['status'],
                    response_dct['pageContent'],
                    response_dct['pageContentPlainText'])
        except KeyError as err:
            raise IOError("Malformed page-response object from phantomjscloud")


    def scrape(self, url=None, urls=None):
        """Either one url, or a list of urls. Returns page-response tuples"""
        if url and not urls:
            urls = [url]

        post_body = json.dumps(self.get_batch_request(urls=urls))

        resp = self.API(self.API_URL).POST(data=post_body,
            headers={'content-type': 'application/json'})

        # resp looks like {u'status': u'success',
        #               u'callbackUrl': u'http://api.phantomjscloud.com/...'}
        resp_dct = resp.json()
        if resp_dct.get('status') != 'success':
            raise IOError("phantomjscloud returned '{0}' instead of 'success'".format(
                resp_dct.get('status')))

        callback_url = resp_dct.get('callbackUrl')
        print "got callback url: {0}".format(callback_url)

        pages = self.get_batch_callback_response(callback_url)
        if len(pages) != len(urls):
            raise ValueError("phantomjscloud didn't give us the same number of pages?!")

        return pages


class ProductScraper(Scraper):
    def _get_product(self, url):
        try:
            product = Product.objects.get(store=self.store, url=url)
        except Product.DoesNotExist:
            product = Product(store=self.store, url=url)

        return product

    def _process_image(self, original_url, product):
        """
        This function uploads the image from the url and adds all necessary data to the image object

        If no image object is passed in, it creates a ProductImage as the default image object type
        """

        try:
            image = ProductImage.objects.get(original_url=original_url, product=product)
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
        if url is None and name is None:
            raise ScraperException('at least one of url or name must be provided to add to a category')

        if not name:
            name = ''
        
        name = name.lower()

        try:
            if not name:
                category = Category.objects.get(store=self.store, url=url)
            else:
                category = Category.objects.get(store=self.store, name__iexact=name)
        except Category.DoesNotExist:
            # if the category does not exist, create it
            if not name:
                raise ScraperException('"name" must be provided if category does not exist')
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


class ContentScraper(Scraper):
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
