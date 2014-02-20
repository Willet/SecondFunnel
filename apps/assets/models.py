from django.core import serializers
from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.fields \
    import CreationDateTimeField, ModificationDateTimeField
from jsonfield import JSONField


class BaseModel(models.Model):

    created_at = CreationDateTimeField()
    updated_at = ModificationDateTimeField()

    class Meta:
        abstract = True


class Store(BaseModel):

    staff = models.ManyToManyField(User, related_name='stores')

    name = models.CharField(max_length=1024)
    description = models.TextField(null=True)
    slug = models.CharField(max_length=64)

    default_theme = models.ForeignKey('pinpoint.StoreTheme', related_name='store', blank=True, null=True)

    public_base_url = models.URLField(help_text="e.g. explore.nativeshoes.com", blank=True, null=True)


class Product(BaseModel):

    store = models.ForeignKey(Store, null=False)

    name = models.CharField(max_length=1024)
    description = models.TextField(null=True)
    details = models.TextField(null=True)
    url = models.TextField()
    sku = models.CharField(max_length=255)
    price = models.CharField(max_length=16)  # DEFER: could make more sense to be an integer (# of cents)

    default_image = models.ForeignKey('ProductImage', related_name='default_image', null=True)

    last_scraped_at = models.DateTimeField(null=True)

    ## for custom, potential per-store additional fields
    ## for instance new-egg's egg-score; sale-prices; etc.
    attributes = JSONField(null=True)


class ProductImage(BaseModel):

    product = models.ForeignKey(Product, null=False)

    url = models.TextField()
    original_url = models.TextField()
    file_type = models.CharField(max_length=255, blank=False, null=False)
    file_checksum = models.CharField(max_length=512)
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()


class Content(BaseModel):

    store = models.ForeignKey(Store, null=False)

    source = models.CharField(max_length=255)
    source_url = models.TextField(null=True)
    author = models.CharField(max_length=255, null=True)

    # list of product id's
    tagged_products = models.CommaSeparatedIntegerField(max_length=512, null=True)

    ## all other fields of proxied models will be store in this field
    ## this will allow arbitrary fields, querying all Content
    ## but restrict to only filtering/ordering on above fields
    attributes = JSONField(null=True)


class Image(Content):

    name = models.CharField(max_length=1024)
    description = models.TextField()

    url = models.TextField()
    original_url = models.TextField()
    file_type = models.CharField(max_length=255, blank=False, null=False)
    file_checksum = models.CharField(max_length=512)

    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()


class Video(Content):

    name = models.CharField(max_length=1024)
    description = models.TextField()

    url = models.TextField()
    player = models.CharField(max_length=255, blank=False)
    file_type = models.CharField(max_length=255, blank=False, null=False)
    file_checksum = models.CharField(max_length=512)


class Review(Content):

    product = models.ForeignKey(Product, null=False)

    body = models.TextField()


class Theme(BaseModel):

    store = models.ForeignKey(Store, null=False)

    name = models.CharField(max_length=1024)
    template = models.CharField(max_length=1024)


class Page(BaseModel):

    theme = models.ForeignKey(Theme, null=True)
    theme_settings = JSONField(null=True)

    name = models.CharField(max_length=256)
    url_slug = models.CharField(max_length=128)
    legal_copy = models.TextField(null=True)

    last_published_at = models.DateTimeField(null=True)

    feed = models.ForeignKey('Feed')


class Feed(BaseModel):
    """"""
    feed_algorithm = models.CharField(max_length=64)  # ; e.g. sorted, recommend
    # and other representation specific of the Feed itself
    #
    def get_results(self, num_results=20, algorithm=None):
        """_algorithm overrides feed_algorithm."""



class Tile(BaseModel):

    feed = models.ForeignKey(Feed, null=False)

    template = models.CharField(max_length=128)

    products = models.ManyToManyField(Product)
    content = models.ManyToManyField(Content)

    prioritized = models.BooleanField()


## TODO: REMOVE THIS IN THE FUTURE
class BaseModelNamed(BaseModel):
    """
    The base model to inherit from when a models needs a name.

    @ivar name: The name of this database object.
    @ivar description: The description of this database object.

    @ivar slug: The short label for this database object. Often used in URIs.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    slug = models.SlugField(blank=True, null=True)

    class Meta:
        abstract = True

    def json(self):
        """default method for all models to have a json representation."""
        return serializers.get_serializer("json")().serialize(iter([self]))

    @classmethod
    def from_json(cls, json_data):
        """create an object from data. this is a subclassable stub."""
        return cls(**json_data)
