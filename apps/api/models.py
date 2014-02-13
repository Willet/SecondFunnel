import sys

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
    pass


class Product(BaseModel):

    store = models.ForeignKey(Store, null=False)

    name = models.CharField(max_length=1024)
    description = models.TextField()
    url = models.TextField()
    sku = models.CharField(max_length=255)
    price = models.CharField(max_length=16)


class Content(BaseModel):

    model_type = models.CharField(max_length=20)

    store = models.ForeignKey(Store, null=False)
    source = models.CharField(max_length=255)
    source_url = models.TextField()
    author = models.CharField(max_length=255)

    ## all other fields of proxied models will be store in this field
    ## this will allow arbitrary fields, querying all Content
    ## but restrict to only filtering/ordering on above fields
    attributes = JSONField()

    def __init__(self, *args, **kwargs):
        super(Content, self).__init__(*args, **kwargs)
        if self.type:
            self.__class__ = getattr(sys.modules[__name__], self.model_type)


class Image(Content):

    name = models.CharField(max_length=1024)
    description = models.TextField()

    url = models.TextField()
    file_type = models.CharField(max_length=255, blank=False, null=False)


class Video(Content):

    name = models.CharField(max_length=1024)
    description = models.TextField()

    url = models.TextField()
    player = models.CharField(max_length=255, blank=False)
    file_type = models.CharField(max_length=255, blank=False, null=False)


class Review(Content):

    product = models.ForeignKey(Product, null=False)
    body = models.TextField()


class Theme(BaseModel):

    store = models.ForeignKey(Store, null=False)
    name = models.CharField(max_length=1024)
    template = models.CharField(max_length=1024)


class Page(BaseModel):

    theme = models.ForeignKey(Theme, null=True)


class Tile(BaseModel):

    page = models.ForeignKey(Page, null=False)

    products = models.ManyToManyField(Product)
    content = models.ManyToManyField(Content)
