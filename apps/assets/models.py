from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django_extensions.db.fields \
    import CreationDateTimeField, ModificationDateTimeField
from jsonfield import JSONField
from dirtyfields import DirtyFieldsMixin
from model_utils.managers import InheritanceManager


default_master_size = {
    'master': {
        'width': '100%',
        'height': '100%',
    }
}


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

        try:
            obj = cls.objects.get(**kwargs)
            for key, value in defaults.iteritems():
                try:
                    current_value = getattr(obj, key, None)
                except ObjectDoesNotExist as err:
                    # tried to read object reference that currently
                    # points to nothing. ignore it and set the attribute.
                    # a subclass.DoesNotExist, whose reference I don't know
                    current_value = err

                if current_value != value:
                    setattr(obj, key, value)
                    updated = True

        except cls.DoesNotExist:
            update_kwargs = dict(defaults.items())
            update_kwargs.update(kwargs)
            obj = cls(**update_kwargs)
            created = True

        if created or updated:
            obj.save()

        return (obj, created, updated)

    def save(self, *args, **kwargs):
        self.full_clean()
        # self.is_dirty() does not take JSONFields into account
        super(BaseModel, self).save(*args, **kwargs)

    def to_json(self):
        """default method for all models to have a json representation."""
        return serializers.get_serializer("json")().serialize(iter([self]))


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

    default_image = models.ForeignKey('ProductImage', related_name='default_image',
                                      blank=True, null=True)

    last_scraped_at = models.DateTimeField(blank=True, null=True)

    ## for custom, potential per-store additional fields
    ## for instance new-egg's egg-score; sale-prices; etc.
    attributes = JSONField(null=True)

    def to_json(self):
        product_images = self.product_images.all()

        dct = {
            "url": self.url,
            "price": self.price,
            "description": self.description,
            "name": self.name,
            "images": [image.to_json() for image in product_images],
        }

        # if default image is missing...
        if self.default_image:
            dct["default-image"] = str(self.default_image.old_id or
                self.default_image.id)
        elif len(product_images) > 0:
            # fall back to first image
            dct["default-image"] = str(product_images[0].old_id)

        return dct


class ProductImage(BaseModel):
    """An Image-like model class that is explicitly an image depicting
    a product, rather than any other kind.
    """
    old_id = models.IntegerField(unique=True)

    product = models.ForeignKey(Product, related_name="product_images")

    url = models.TextField()  # 2f.com/.jpg
    original_url = models.TextField()  # gap.com/.jpg
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)
    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    dominant_color = models.CharField(max_length=32, blank=True, null=True)

    attributes = JSONField(blank=True, null=True, default={})

    def __init__(self, *args, **kwargs):
        super(ProductImage, self).__init__(*args, **kwargs)

    def to_json(self):
        dct = {
            "format": self.file_type or "jpg",
            "type": "image",
            "dominant-color": self.dominant_color or "transparent",
            # TODO: deprecate "colour" to match up with CSS attr names
            "dominant-colour": self.dominant_color or "transparent",
            "url": self.url,
            "id": str(self.old_id or self.id),
            "sizes": self.attributes.get('sizes', default_master_size)
        }
        return dct


class Content(BaseModel):
    # Content.objects object for deserializing Content models as subclasses
    objects = InheritanceManager()

    old_id = models.IntegerField(unique=True)

    store = models.ForeignKey(Store)

    url = models.TextField()  # 2f.com/.jpg
    source = models.CharField(max_length=255)
    source_url = models.TextField(blank=True, null=True)  # gap/.jpg
    author = models.CharField(max_length=255, blank=True, null=True)

    tagged_products = models.ManyToManyField(Product, null=True)

    ## all other fields of proxied models will be store in this field
    ## this will allow arbitrary fields, querying all Content
    ## but restrict to only filtering/ordering on above fields
    attributes = JSONField(null=True)

    def __init__(self, *args, **kwargs):
        super(Content, self).__init__(*args, **kwargs)
        if not self.attributes:
            self.attributes = {}

    def to_json(self):
        """subclasses may implement their own to_json methods that
        :returns dict objects.
        """
        dct = {
            'store-id': str(self.store.old_id if self.store else 0),
            'source': self.source,
            'source_url': self.source_url,
            'url': self.url or self.source_url,
            'author': self.author,
        }

        if self.tagged_products.count() > 0:
            dct['related-products'] = []

        for product in (self.tagged_products
                            .select_related('default_image', 'product_images')
                            .all()):
            try:
                dct['related-products'].append(product.to_json())
            except Product.DoesNotExist:
                pass  # ?

        return dct


class Image(Content):

    name = models.CharField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    original_url = models.TextField()
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)

    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    dominant_color = models.CharField(max_length=32, blank=True, null=True)

    def to_json(self, expand_products=True):
        """Only Images (not ProductImages) can have related-products."""
        dct = {
            "format": self.file_type,
            "type": "image",
            "dominant-color": self.dominant_color or "transparent",
            # TODO: deprecate "colour" to match up with CSS attr names
            "dominant-colour": self.dominant_color or "transparent",
            "url": self.url or self.source_url,
            "id": str(self.old_id or self.id),
            "sizes": self.attributes.get('sizes', default_master_size),
        }
        if expand_products:
            # turn django's string list of strings into a real list of ids
            dct["related-products"] = [x.to_json() for x in self.tagged_products.all()]
        else:
            dct["related-products"] = [x.old_id for x in self.tagged_products.all()]

        return dct


class Video(Content):

    name = models.CharField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    player = models.CharField(max_length=255)
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)

    # e.g. oHg5SJYRHA0
    original_id = models.CharField(max_length=255, blank=True, null=True)

    def to_json(self):
        dct = super(Video, self).to_json()

        # videos *need* original-id and original-url
        dct["original-id"] = self.original_id or self.id
        dct["original-url"] = self.source_url or self.url

        return dct


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


class Page(BaseModel):

    store = models.ForeignKey(Store)

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
    # use content.select_subclasses() instead of content.all()!
    content = models.ManyToManyField(Content)

    prioritized = models.BooleanField()

    # miscellaneous attributes, e.g. "is_banner_tile"
    attributes = JSONField(null=True, default={})

    def to_json(self):
        # attributes from tile itself
        dct = {
            'tile-id': self.old_id or self.id,
            'template': self.template,
            'prioritized': self.prioritized,
        }

        product_count, content_count = self.products.count(), self.content.count()

        if product_count > 0 and content_count > 0:
            # combobox
            print "Rendering tile of type  combobox"
            dct.update(self._to_combobox_tile_json())
        elif product_count > 0 and content_count == 0:
            # product
            print "Rendering tile of type  product"
            dct.update(self._to_product_tile_json())
        elif product_count == 0 and content_count > 0:
            # (assorted) content
            print "Rendering tile of type  content"
            dct.update(self._to_content_tile_json())
        elif self.template == 'banner' or self.attributes.get('is_banner_tile',
                                                              False):
            dct.update({
                'redirect-url': self.attributes.get('redirect_url') or \
                    (self.content.select_subclasses()[0].source_url
                     if self.content.count()
                     else '')
            })
        else:
            dct.update({'warning': 'Tile has neither products nor content!'})

        return dct

    def _to_combobox_tile_json(self):
        # there are currently no combobox json formats.
        return self._to_content_tile_json()

    def _to_product_tile_json(self):
        return (self.products
                    .select_related('product_images')
                    [0]
                    .to_json())

    def _to_content_tile_json(self):
        # currently, there are only single-content tiles, so
        # pick the first content and jsonify it
        return (self.content
                    .prefetch_related('tagged_products')
                    .select_subclasses()
                    [0]
                    .to_json())
