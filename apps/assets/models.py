import math

from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import Serializer
from django.db import models
from django_extensions.db.fields \
    import CreationDateTimeField, ModificationDateTimeField
from django.utils import timezone

from jsonfield import JSONField
from dirtyfields import DirtyFieldsMixin
from model_utils.managers import InheritanceManager
from apps.intentrank.serializers import *


default_master_size = {
    'master': {
        'width': '100%',
        'height': '100%',
    }
}


class BaseModel(models.Model, DirtyFieldsMixin):
    created_at = CreationDateTimeField()
    updated_at = ModificationDateTimeField()

    serializer = Serializer

    class Meta:
        abstract = True

    def days_since_creation(self):
        return (timezone.now() - self.created_at).days

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

    def get(self, key, default):
        """Duck-type a <dict>'s get() method to make CG transition easier.

        Remove when no longer necessary.
        """
        return getattr(self, name=key, default=default)

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

    public_base_url = models.URLField(help_text="e.g. explore.nativeshoes.com",
                                      blank=True, null=True)

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

    serializer = ProductSerializer

    def to_json(self):
        return self.serializer().to_json([self])


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

    serializer = ContentSerializer

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

    serializer = ContentTileSerializer

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

    caption = models.CharField(max_length=255, blank=True, default="")
    username = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, null=True)

    player = models.CharField(max_length=255)
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)

    # e.g. oHg5SJYRHA0
    original_id = models.CharField(max_length=255, blank=True, null=True)

    serializer = VideoSerializer

    def to_json(self):
        return self.serializer().to_json([self])


class Review(Content):
    product = models.ForeignKey(Product)

    body = models.TextField()


class Theme(BaseModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    template = models.CharField(max_length=1024,
                                # backward compatibility for pages that don't specify themes
                                default="https://s3.amazonaws.com/elasticbeanstalk-us-east-1-056265713214/static-misc-secondfunnel/themes/campaign_base.html")

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
    def to_json(self):
        serializer = FeedSerializer(self.tiles.all())
        return serializer.serialize()


class Page(BaseModel):
    store = models.ForeignKey(Store)

    name = models.CharField(max_length=256)  # e.g. Lived In
    old_id = models.IntegerField(unique=True)

    theme = models.ForeignKey(Theme, related_name='page', blank=True, null=True)

    # attributes named differently
    theme_settings = JSONField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    url_slug = models.CharField(max_length=128)  # e.g. livedin
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
    # used to calculate the score for a tile
    # a bigger s value does not necessarily mean a bigger score
    starting_score = models.FloatField(default=0)

    clicks = models.PositiveIntegerField(default=0)

    old_id = models.IntegerField(unique=True, db_index=True)

    # <Feed>.tiles.all() gives you... all its tiles
    feed = models.ForeignKey(Feed, related_name='tiles')

    template = models.CharField(max_length=128)

    products = models.ManyToManyField(Product)
    # use content.select_subclasses() instead of content.all()!
    content = models.ManyToManyField(Content)

    prioritized = models.BooleanField()

    # variable used for popularity, the bigger the value, the faster popularity de-values
    popularity_devalue_rate = 0.15

    # miscellaneous attributes, e.g. "is_banner_tile"
    attributes = JSONField(null=True, default={})

    def click(self):
        self.clicks += 1
        # the value used to increase starting_score per click
        update_score = Tile.popularity_devalue_rate * self.days_since_creation()
        starting_score = self.starting_score
        self.starting_score = max(starting_score, update_score) + math.log(
            1 + math.exp(min(starting_score, update_score) - max(starting_score, update_score)))
        self.save()

    @property
    def score(self):
        # returns the score of the tile based on the starting_score and how long ago the tile was created
        return math.exp(self.starting_score - Tile.popularity_devalue_rate *
                        self.days_since_creation())

    @property
    def log_score(self):
        # the lower the ratio, the bigger the range between low and high scores
        ratio = 1.5
        score = self.score
        # returns the log of a score with the smallest value being 1
        # makes sure that small scores do not get large log values
        return math.log(score + (ratio if score > 2 * ratio else (ratio - score / 2)), ratio)

    def to_json(self):
        # determine what kind of tile this is
        serializer = None
        if self.template == 'image':
            serializer = ContentTileSerializer()
        else:
            try:
                if not serializer:
                    serializer = globals()[self.template.capitalize() + 'TileSerializer']()
            except:  # cannot find e.g. 'Youtube'TileSerializer -- use default
                serializer = TileSerializer()

        return serializer.to_json([self])
