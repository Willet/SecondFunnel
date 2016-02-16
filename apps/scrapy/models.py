from hashlib import md5

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from apps.assets.models import Product


validator = URLValidator()


class PlaceholderProduct(Product):
    """
    Sometimes adding a product fails, but we want a record that it should exist

    Only requirement is a valid URL for future scraping
    
    Stored in same table as Product -> can't assign new fields!
    """
    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.placeholder = True
        self.price = 0
        self.sale_price = None
        self.in_stock = False

        if not self.name:
            self.name = "placeholder"
        if not self.sku:
            # Make-up a temporary, unique SKU
            self.sku = u"placeholder-{}".format(md5(self.url).hexdigest())
        
        super(PlaceholderProduct, self).save(*args, **kwargs)

    def clean_fields(self, exclude=None):
        if exclude is None:
            exclude = []

        if not 'url' in exclude:
            try:
                validator(self.url)
            except ValidationError:
                raise ValidationError({'url': [u'Must be a valid url']})
