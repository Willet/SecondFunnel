from apps.assets.models import Category, ProductImage
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

    def __init__(self, store):
        self.store = store

    def get_regex(self, values, **kwargs):
        """
        The list of regexs that match the urls for this scraper
        """
        raise NotImplementedError

    def parse_url(self, url, values, **kwargs):
        """
        Optional method
        Returns a condensed url from the passed in url
        """
        return url

    def next_scraper(self, values, **kwargs):
        """
        Optional Method
        Returns a scraper if there is a need to explicitly define the next scraper
        If None is returned, the controller decides what to do next based on the scraper regexs
        """
        return None

    def _wrap_regex(self, regex, has_parameters=False, allow_parameters=True):
        """
        Makes creation of regexes easier, wraps with matching for https? at the beginning
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

    def scrape(self, driver, url, values, **kwargs):
        """
        The method used to run the scraper
        For category scrapers, a store is also added to the arguments
        For detail scrapers, a product or content object is added to the arguments

        Models must be returned using yield

        If it is a content scraper, the content must be created inside the scraper
        if the passed in content is None
        """
        raise NotImplementedError


class ProductScraper(Scraper):
    def _process_image(self, original_url, product):
        """
        This function uploads the image from the url and adds all necessary data to the image object

        If no image object is passed in, it creates a ProductImage as the default image object type
        """

        try:
            image = ProductImage.objects.get(original_url=original_url, product=product)
        except ProductImage.DoesNotExist:
            image = ProductImage(original_url=original_url, product=product)
            # TODO: remove old_id
            last = ProductImage.objects.all().order_by('-old_id')[0]
            image.old_id = last.old_id + 1

        print('processing image - ' + original_url)
        data = process_image(original_url, create_image_path(self.store.id))
        image.url = data.get('url')
        image.file_type = data.get('format')
        image.dominant_color = data.get('dominant_colour')

        # save the image
        image.save()

        if product and not product.default_image:
            product.default_image = image
            product.save()

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

        try:
            if url is None:
                category = Category.objects.get(store=self.store, name=name)
            else:
                category = Category.objects.get(store=self.store, url=url)
        except Category.DoesNotExist:
            # if the category does not exist, create it
            if url is None or name is None:
                raise ScraperException('url and name must be provided if category does not exist')
            category = Category(store=self.store, name=name, url=url)
            category.save()

        # add the product to the category
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

        print('processing image - ' + source_url)
        data = process_image(source_url, create_image_path(self.store.id))
        image.url = data.get('url')
        image.file_type = data.get('format')
        image.dominant_color = data.get('dominant_colour')
        image.source_url = source_url

        return image


class ContentCategoryScraper(ContentScraper):
    def has_next_scraper(self, values, **kwargs):
        return True


class ContentDetailScraper(ContentScraper):
    pass