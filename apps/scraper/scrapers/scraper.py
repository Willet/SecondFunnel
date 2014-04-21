from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from apps.assets.models import Category, ProductImage, Product
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path


class ScraperException(Exception):
    pass


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
        try:
            self.driver = webdriver.PhantomJS(service_log_path='/tmp/ghostdriver.log')
        except WebDriverException:
            self.driver = webdriver.PhantomJS(service_log_path='/tmp/ghostdriver.log')
        self.store = store

    def parse_url(self, url, values, **kwargs):
        """
        Optional method
        Returns a condensed url from the passed in url
        """
        return url

    @staticmethod
    def _wrap_regex(regex, has_parameters=False, allow_parameters=True):
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

    def scrape(self, url, values, **kwargs):
        """
        The method used to run the scraper

        yield is used to return dictionaries with the required variables
        url must be included in the dictionary if another scraper must be run after this one
        product or content must be included if no scraper should be run after this one
        scraper can be included to explicitly define the next scraper
        """
        raise NotImplementedError


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
            print('\nprocessing image - ' + original_url)
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
            print('\nimage has already been processed')

        print(image.to_json())

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
                raise ScraperException('name must be provided if category does not exist')
            category = Category(store=self.store, name=name)

        if url:
            category.url = url
        if name:
            category.name = name
        category.save()

        # add the product to the category
        print('adding product to category ' + name)
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

        print('')
        print('processing image - ' + source_url)
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
