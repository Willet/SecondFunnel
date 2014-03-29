from apps.assets.models import Category, ProductImage, Image
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import create_image_path

class ScraperException(Exception):
    pass

class Scraper(object):

    PRODUCT_DETAIL = 'product-detail'
    PRODUCT_CATEGORY = 'product-category'
    CONTENT_DETAIL = 'content-detail'
    CONTENT_CATEGORY = 'content-category'

    def __init__(self, store, dry_run):
        self.store = store
        self.dry_run = dry_run

    # the regex or list of regexs that match the url's that this scraper can scrape
    def get_regex(self, values={}, **kwargs):
        raise NotImplementedError

    # is passed the original url plus any values that are being passed to the scraper
    # return a string which is used as the new url
    def parse_url(self, url, values={}, **kwargs):
        return url

    # returns the type of scraper, types are defined as constants in the Scraper class
    def get_type(self, values={}, **kwargs):
        raise NotImplementedError

    # if there is a need to explicitly state the detail scraper for a category scraper
    def next_scraper(self, values={}, **kwargs):
        return None

    def _process_image(self, url, image_model=None, product=None):

        if image_model is None and product is None:
            raise ScraperException('no model or product provided for processing image')

        if image_model is None:
            try:
                image_model = ProductImage.objects.get(store=self.store, original_url=url, product=product)
            except ProductImage.DoesNotExist:
                image_model = ProductImage(store=self.store, original_url=url, product=product)
        else:
            if isinstance(image_model, Image):
                image_model.source_url = url
            elif isinstance(image_model, ProductImage):
                image_model.original_url = url

        # temporary do not upload images
        if not self.dry_run and False:
            data = process_image(url, create_image_path(self.store.id))
            image_model.url = data.get('url')
            image_model.file_type = data.get('format')
            image_model.dominant_color = data.get('dominant_colour')
        else:
            image_model.url = url

        if not self.dry_run:
            image_model.save()

        if product and not product.default_image:
            product.default_image = image_model

        if isinstance(image_model, ProductImage):
            print('creted image')
            print(image_model.to_json())
        return image_model

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

    # the actual scraper
    # for category scrapers, a store is also added to the arguments
    # for detail scrapers, a product or content object is added to the arguments
    def scrape(self, driver, url, values={}, **kwargs):
        raise NotImplementedError

    def validate(self, values={}, **kwargs):
        return True