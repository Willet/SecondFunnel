from django.core import serializers
from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.fields \
    import CreationDateTimeField, ModificationDateTimeField
from jsonfield import JSONField
from dirtyfields import DirtyFieldsMixin

from apps.pinpoint.utils import read_remote_file, read_a_file


class BaseModel(models.Model, DirtyFieldsMixin):

    created_at = CreationDateTimeField()
    updated_at = ModificationDateTimeField()

    class Meta:
        abstract = True

    @classmethod
    def update_or_create(cls, defaults=None, **kwargs):
        """Like Model.objects.get_or_create, either gets, updates, or creates
        a model based on current state. Arguments are the same as the former.

        Examples:
        >>> Store.update_or_create(id=2, defaults={"old_id": 3})
        (<Store: Store object>, True, False)  # created
        >>> Store.update_or_create(id=2, defaults={"old_id": 3})
        (<Store: Store object>, False, False)  # found
        >>> Store.update_or_create(id=2, old_id=4)
        (<Store: Store object>, False, True)  # updated

        :raises <AllSortsOfException>s, depending on input
        :returns tuple  (object, updated, created)
        """
        updated = created = False

        if not defaults:
            defaults = {}

        # a kwargs-priority full set of kwargs
        update_or_create_kwargs = dict(defaults.items() + kwargs.items())
        try:
            obj = cls.objects.get(**kwargs)
            for field in update_or_create_kwargs:
                if getattr(obj, field, None) != update_or_create_kwargs.get(field):
                    setattr(obj, field, update_or_create_kwargs[field])
                    updated = True
            if updated:
                obj.save()
        except cls.DoesNotExist:
            obj = cls(**update_or_create_kwargs)
            obj.save()
            created = True

        return (obj, created, updated)

    def save(self, *args, **kwargs):
        if self.is_dirty():
            super(BaseModel, self).save(*args, **kwargs)
        else:
            print "[INFO] {0} was not saved because " \
                  "it was not modified".format(repr(self))


class Store(BaseModel):

    old_id = models.IntegerField(unique=True)

    staff = models.ManyToManyField(User, related_name='stores')

    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    slug = models.CharField(max_length=64)

    default_theme = models.ForeignKey('Theme', related_name='store', blank=True, null=True)

    public_base_url = models.URLField(help_text="e.g. explore.nativeshoes.com", blank=True, null=True)

    @classmethod
    def from_json(cls, json_data):
        """@deprecated for replacing the Campaign Model. Use something else.
        """
        if 'theme' in json_data:
            json_data['theme'] = Theme(template=json_data['theme'])

        instance = cls()
        for field in json_data:
            setattr(instance, field, json_data[field])
        return instance


class Product(BaseModel):

    old_id = models.IntegerField(unique=True)

    store = models.ForeignKey(Store)

    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    url = models.TextField()
    sku = models.CharField(max_length=255)
    price = models.CharField(max_length=16)  # DEFER: could make more sense to be an integer (# of cents)

    default_image = models.ForeignKey('ProductImage', related_name='default_image', blank=True, null=True)

    last_scraped_at = models.DateTimeField(blank=True, null=True)

    ## for custom, potential per-store additional fields
    ## for instance new-egg's egg-score; sale-prices; etc.
    attributes = JSONField(null=True)


class ProductImage(BaseModel):

    old_id = models.IntegerField(unique=True)

    product = models.ForeignKey(Product, related_name="product_images")

    url = models.TextField()  # 2f.com/.jpg
    original_url = models.TextField()  # gap.com/.jpg
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)
    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    dominant_colour = models.CharField(max_length=32, blank=True, null=True)

    attributes = JSONField(blank=True, null=True)

    def to_json(self):
        return {
            "format": self.file_type,
            "type": "image",
            "dominant-colour": self.dominant_color or "transparent",  # TODO: colour
            "url": self.url,
            "id": self.old_id or self.id,
            "sizes": self.attributes.get('sizes')
        }


class Content(BaseModel):

    old_id = models.IntegerField(unique=True)

    store = models.ForeignKey(Store)

    source = models.CharField(max_length=255)
    source_url = models.TextField(blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)

    # list of product id's
    tagged_products = models.CommaSeparatedIntegerField(max_length=512, blank=True, null=True)

    ## all other fields of proxied models will be store in this field
    ## this will allow arbitrary fields, querying all Content
    ## but restrict to only filtering/ordering on above fields
    attributes = JSONField(null=True)


class Image(Content):

    name = models.CharField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    url = models.TextField()
    original_url = models.TextField()
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)

    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    dominant_colour = models.CharField(max_length=32, blank=True, null=True)

    to_json = ProductImage.to_json  # use the same json format as other images


class Video(Content):

    name = models.CharField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    url = models.TextField()
    player = models.CharField(max_length=255)
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)


class Review(Content):

    product = models.ForeignKey(Product)

    body = models.TextField()


class Theme(BaseModel):

    name = models.CharField(max_length=1024, blank=True, null=True)
    template = models.CharField(max_length=1024)

    # @deprecated for page generator
    CUSTOM_FIELDS = {
        'opengraph_tags': 'pinpoint/campaign_opengraph_tags.html',
        'head_content': 'pinpoint/campaign_head.html',
        'body_content': 'pinpoint/campaign_body.html',
        'campaign_config': 'pinpoint/campaign_config.html',
        'js_templates': 'pinpoint/default_templates.html'
    }


class Feed(BaseModel):
    """"""
    feed_algorithm = models.CharField(max_length=64, blank=True, null=True)  # ; e.g. sorted, recommend
    # and other representation specific of the Feed itself
    #
    def get_results(self, num_results=20, algorithm=None):
        """_algorithm overrides feed_algorithm."""


class Page(BaseModel):

    old_id = models.IntegerField(unique=True)

    theme = models.ForeignKey(Theme, related_name='page', blank=True, null=True)
    theme_settings = JSONField(blank=True, null=True)

    name = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)
    url_slug = models.CharField(max_length=128)
    legal_copy = models.TextField(blank=True, null=True)

    last_published_at = models.DateTimeField(blank=True, null=True)

    feed = models.ForeignKey(Feed)

    @property
    def template(self):
        theme_settings = self.theme_settings or {}
        return theme_settings.get('template', 'hero')

    @template.setter
    def template(self, value):
        if not self.theme_settings:
            self.theme_settings = {}
        self.theme_settings['template'] = value

    @classmethod
    def from_json(cls, json_data):
        """@deprecated for replacing the Campaign Model. Use something else.
        """
        if 'theme' in json_data:
            json_data['theme'] = Theme(template=json_data['theme'])

        instance = cls()
        for field in json_data:
            setattr(instance, field, json_data[field])
        return instance


class Tile(BaseModel):

    old_id = models.IntegerField(unique=True)

    # <Feed>.tiles.all() gives you... all its tiles
    feed = models.ForeignKey(Feed, related_name='tiles')

    template = models.CharField(max_length=128)

    products = models.ManyToManyField(Product)
    content = models.ManyToManyField(Content)

    prioritized = models.BooleanField()

    @property
    def images(self):
        """can't filter by subclassed FK? not sure if..."""
        image_list = []
        for content in self.content.all():
            if isinstance(content, Image):
                image_list.append(content)
        return image_list

    def to_json(self):
        first_product = self.products.all()[:1].get()
        product_images = first_product.product_images.all()
        content_images = self.images
        return {
            "default-image": first_product.default_image.id,
            "url": first_product.url,
            "price": first_product.price,
            "description": first_product.description,
            "name": first_product.name,
            "images": [image.to_json() for image in content_images], # + [image.to_json() for image in product_images],
            "tile-id": self.old_id or self.id,
            "template": self.template
        }


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
