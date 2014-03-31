from apps.assets.models import Category, ProductImage, Image
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path

class ScraperException(Exception):
    pass

class Scraper(object):
    """
    Base class for all scrapers

    The value variable is a dictionary that is passed around by the controller
    to all functions in the scraper and to all sub-scrapers, it can be added to
    by any function and is not changed by the controller
    """

    PRODUCT_DETAIL = 'product-detail'
    PRODUCT_CATEGORY = 'product-category'
    CONTENT_DETAIL = 'content-detail'
    CONTENT_CATEGORY = 'content-category'

    def __init__(self, store, dry_run):
        self.store = store
        self.dry_run = dry_run

    def get_regex(self, values={}, **kwargs):
        """
        The regex or list of regexs that match the urls for this scraper
        """
        raise NotImplementedError

    def parse_url(self, url, values={}, **kwargs):
        """
        Optional method
        Returns a condensed url from the passed in url
        """
        return url

    def get_type(self, values={}, **kwargs):
        """
        Returns the type of scraper, all types are defined as constants in the scraper class
        """
        raise NotImplementedError

    def next_scraper(self, values={}, **kwargs):
        """
        Optional Method
        Returns a scraper if there is a need to explicitly define the next scraper
        If None is returned, the controller decides what to do next based on the scraper regexs
        """
        return None

    def _wrap_regex(self, regex, has_parameters=False, allow_parameters=True):
        regex = r'^(?:https?://)?' + regex
        if allow_parameters:
            if has_parameters:
                regex += r'(?:&[^\?/]*)?'
            else:
                regex += r'(?:\?[^\?/]*)?'
        regex += r'(?:#.*)?$'
        return regex

    def _process_image(self, url, image=None, product=None):

        if image is None and product is None:
            raise ScraperException('no model or product provided for processing image')

        if image is None:
            try:
                image = ProductImage.objects.get(store=self.store, original_url=url, product=product)
            except ProductImage.DoesNotExist:
                image = ProductImage(store=self.store, original_url=url, product=product)
        else:
            if isinstance(image, Image):
                image.source_url = url
            elif isinstance(image, ProductImage):
                image.original_url = url

        # temporary do not upload images
        if not self.dry_run and False:
            data = process_image(url, create_image_path(self.store.id))
            image.url = data.get('url')
            image.file_type = data.get('format')
            image.dominant_color = data.get('dominant_colour')
        else:
            image.url = url

        if not self.dry_run:
            image.save()

        if product and not product.default_image:
            product.default_image = image

        if isinstance(image, ProductImage):
            print('created image')
            print(image.to_json())
        return image

    def _add_to_category(self, product, name=None, url=None):
        if url is None and name is None:
            raise ScraperException('at least one of url or name must be provided to add to a category')

        try:
            if url is None:
                category = Category.objects.get(store=self.store, name=name)
            else:
                category = Category.objects.get(store=self.store, url=url)
        except Category.DoesNotExist:
            if url is None or name is None:
                raise ScraperException('url and name must be provided if category does not exist')
            category = Category(store=self.store, name=name, url=url)

        if not self.dry_run:
            category.save()
            category.products.add(product)

    def scrape(self, driver, url, values={}, **kwargs):
        """
        The method used to run the scraper
        For category scrapers, a store is also added to the arguments
        For detail scrapers, a product or content object is added to the arguments

        If the scraper is a category scraper, models must be returned using yield

        If it is a content scraper, the content must be created inside the scraper
        if the passed in content is None
        """
        raise NotImplementedError

    def validate(self, values={}, **kwargs):
        """
        Optional method
        Is used to validate products or content
        If false is returned, the model is not saved or passed on to any next scrapers
        """
        return True