from hashlib import md5

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from apps.assets.models import Product


validator = URLValidator()


class PlaceholderProduct(Product):
    """
    Sometimes adding a product fails, but we want a record that it should exist
    Stored in same table as Product -> can't assign new fields!

    PlaceholderProduct is DEFINED by name = "placeholder". Is automatically filtered
    out by IntentRank
    """
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        try:
            validator(kwargs['url'])
        except (KeyError, ValidationError):
            raise ValueError('PlaceholderProduct must be initialized with a valid url')
        super(PlaceholderProduct, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.name = "placeholder"
        self.price = 0
        self.in_stock = False
        if not self.sku:
            # Make-up a temporary, unique SKU
            self.sku = "placeholder-{}".format(md5(self.url).hexdigest())
        super(PlaceholderProduct, self).save(*args, **kwargs)