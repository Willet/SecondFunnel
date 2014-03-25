import math
import datetime
import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.serializers.json import Serializer
from django.db import models
from django.db.models import Q
from django_extensions.db.fields import CreationDateTimeField
from django.utils import timezone
from jsonfield import JSONField
from dirtyfields import DirtyFieldsMixin
from model_utils.managers import InheritanceManager

from apps.intentrank.serializers import *
from apps.utils import returns_unicode


default_master_size = {
    'master': {
        'width': '100%',
        'height': '100%',
    }
}


class BaseModel(models.Model, DirtyFieldsMixin):
    created_at = CreationDateTimeField(); created_at.editable = True

    # To change this value, use model.save(skip_updated_at=True)
    updated_at = models.DateTimeField()

    serializer = Serializer

    class Meta:
        abstract = True

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __unicode__(self):
        """Changes display of models in the django admin.

        http://stackoverflow.com/a/5853966/1558430
        """
        if hasattr(self, 'name'):
            return u'({class_name} #{obj_id}) {obj_name}'.format(
                class_name=self.__class__.__name__,
                obj_id=self.pk,
                obj_name=getattr(self, 'name', ''))

        return u'{class_name} #{obj_id}'.format(
            class_name=self.__class__.__name__,
            obj_id=self.pk)

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

    def get(self, key, default=None):
        """Duck-type a <dict>'s get() method to make CG transition easier.

        Also looks into the attributes JSONField if present.
        """
        attr = getattr(self, key, None)
        if attr:
            return attr
        if hasattr(self, 'attributes'):
            return self.attributes.get(key, default=default)

    def save(self, *args, **kwargs):
        # http://stackoverflow.com/a/7502498/1558430
        # allows modification of a last-modified timestamp
        if not kwargs.pop('skip_updated_at', False):
            self.updated_at = datetime.datetime.now(
                tz=pytz.timezone(settings.TIME_ZONE))

        self.full_clean()
        super(BaseModel, self).save(*args, **kwargs)

    def to_json(self):
        """default method for all models to have a json representation."""
        return self.serializer().serialize(iter([self]))


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
    old_id = models.IntegerField(blank=True, null=True)

    store = models.ForeignKey(Store)

    available = models.BooleanField(default=False)

    name = models.CharField(blank=True, null=True, max_length=1024)
    description = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    url = models.TextField()
    sku = models.CharField(blank=True, null=True, max_length=255)
    price = models.CharField(blank=True, null=True, max_length=16)  # DEFER: could make more sense to be an integer (# of cents)

    default_image = models.ForeignKey('ProductImage', related_name='default_image',
                                      blank=True, null=True, on_delete=models.SET_NULL)

    last_scraped_at = models.DateTimeField(blank=True, null=True)

    ## for custom, potential per-store additional fields
    ## for instance new-egg's egg-score; sale-prices; etc.
    attributes = JSONField(blank=True, null=True, default={})

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
    def _validate_status(status):
        allowed =["approved", "rejected", "needs-review"]
        if status not in allowed:
            raise ValidationError("{0} is not an allowed status; "
                                  "choices are {1}".format(status, allowed))

    # Content.objects object for deserializing Content models as subclasses
    objects = InheritanceManager()

    old_id = models.IntegerField(unique=True)

    store = models.ForeignKey(Store, related_name='content')

    url = models.TextField()  # 2f.com/.jpg
    source = models.CharField(max_length=255)
    source_url = models.TextField(blank=True, null=True)  # gap/.jpg
    author = models.CharField(max_length=255, blank=True, null=True)

    tagged_products = models.ManyToManyField(Product, null=True)

    ## all other fields of proxied models will be store in this field
    ## this will allow arbitrary fields, querying all Content
    ## but restrict to only filtering/ordering on above fields
    attributes = JSONField(null=True, blank=True, default={})

    # "approved", "rejected", "needs-review"
    status = models.CharField(max_length=255, blank=True, null=True,
                              default="approved",
                              validators=[_validate_status])

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
    """
    :attr template either a local path or a remote path, e.g.
        "apps/pinpoint/templates/pinpoint/campaign_base.html"
        "apps/pinpoint/static/pinpoint/themes/gap/index.html"
        "https://static-misc-secondfunnel/themes/campaign_base.html"
    """
    name = models.CharField(max_length=1024, blank=True, null=True)
    template = models.CharField(max_length=1024,
        # backward compatibility for pages that don't specify themes
        default="apps/pinpoint/templates/pinpoint/campaign_base.html")

    # @deprecated for page generator
    CUSTOM_FIELDS = {
        'opengraph_tags': 'pinpoint/campaign_opengraph_tags.html',
        'head_content': 'pinpoint/campaign_head.html',
        'body_content': 'pinpoint/campaign_body.html',
        'campaign_config': 'pinpoint/campaign_config.html',
        'js_templates': 'pinpoint/default_templates.html'
    }

    @returns_unicode
    def load_theme(self):
        """download/open the template as a string."""
        from apps.pinpoint.utils import read_a_file, read_remote_file

        if 'static-misc-secondfunnel/themes/gap.html' in self.template:
            # exception for task "Get all pages on tng-test and tng-master using gap theme as code"
            self.template = 'apps/pinpoint/static/pinpoint/themes/gap/index.html'

        local_theme = read_a_file(self.template, '')
        if local_theme:
            return local_theme

        remote_theme = read_remote_file(self.template, '')[0]
        if remote_theme:
            print "[INFO] speed up page load times by placing the theme" \
                  " '{0}' locally.".format(self.template)
            return remote_theme

        print "[WARN] template '{0}' was neither local nor remote".format(
            self.template)
        return self.template


class Feed(BaseModel):
    """"""
    feed_algorithm = models.CharField(max_length=64, blank=True, null=True)  # ; e.g. sorted, recommend
    # and other representation specific of the Feed itself
    def to_json(self):
        serializer = FeedSerializer(self.tiles.all())
        return serializer.serialize()


class Page(BaseModel):
    store = models.ForeignKey(Store, related_name='pages')

    name = models.CharField(max_length=256)  # e.g. Lived In
    old_id = models.IntegerField(unique=True)

    theme = models.ForeignKey(Theme, related_name='page', blank=True, null=True)

    # attributes named differently
    theme_settings = JSONField(blank=True, null=True)

    theme_settings_fields = [
        ('template', 'hero'), ('image_tile_wide', 0.5), ('hide_navigation_bar', ''),
        ('results_threshold', {}), ('desktop_hero_image', ''), ('mobile_hero_image', ''),
        ('intentrank_id', old_id), ('column_width', 240), ('social_buttons', ''),
        ('enable_tracking', "true"), ('ir_base_url', ''), ('ga_account_number', ''),
    ]

    description = models.TextField(blank=True, null=True)
    url_slug = models.CharField(max_length=128)  # e.g. livedin
    legal_copy = models.TextField(blank=True, null=True)

    last_published_at = models.DateTimeField(blank=True, null=True)

    feed = models.ForeignKey(Feed, related_name='page')

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if not self.theme_settings:
            self.theme_settings = {}

    def __getattr__(self, name):
        for (key, default) in self.theme_settings_fields:
            if name == key:
                theme_settings = self.theme_settings or {}
                return theme_settings.get(key, default)
        return super(Page, self).__getattr__(name)

    def __setattr__(self, name, value):
        for (key, default) in self.theme_settings_fields:
            if name == key:
                if not self.theme_settings:
                    self.theme_settings = {}
                self.theme_settings[key] = value
                return
        super(Page, self).__setattr__(name, value)

    def get(self, key, default=None):
        """Duck-type a <dict>'s get() method to make CG transition easier.

        Also looks into the theme_settings JSONField if present.
        """
        attr = getattr(self, key, None)
        if attr:
            return attr
        if hasattr(self, 'theme_settings') and self.theme_settings:
            return self.theme_settings.get(key, default)

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
    old_id = models.IntegerField(unique=True, db_index=True)

    # <Feed>.tiles.all() gives you... all its tiles
    feed = models.ForeignKey(Feed, related_name='tiles')

    template = models.CharField(max_length=128)

    products = models.ManyToManyField(Product)
    # use content.select_subclasses() instead of content.all()!
    content = models.ManyToManyField(Content)

    prioritized = models.BooleanField()

    # if the feed's algorithm is 'generic', then priority is not used.
    # if the feed's algorithm is 'ordered', then prioritized tiles will be
    # sorted using this attribute instead of the tile's created date.
    #   negative values are allowed.
    #   identical values are undeterministic.
    priority = models.IntegerField(null=True, default=0)

    # miscellaneous attributes, e.g. "is_banner_tile"
    attributes = JSONField(blank=True, null=True, default={})

    # used to calculate the score for a tile
    # a bigger starting_score value does not necessarily mean a bigger score
    click_starting_score = models.FloatField(default=0.0)

    view_starting_score = models.FloatField(default=0.0)

    clicks = models.PositiveIntegerField(default=0)

    views = models.PositiveIntegerField(default=0)

    # variable used for popularity, the bigger the value, the faster popularity de-values
    popularity_devalue_rate = 0.15

    # the lower the ratio, the bigger the range between low and high log_scores
    ratio = 1.5

    def add_click(self):
        self.clicks += 1
        # the value used to increase click_starting_score per click
        update_score = Tile.popularity_devalue_rate * self.days_since_creation()
        starting_score = self.click_starting_score
        self.click_starting_score = max(starting_score, update_score) + math.log(
            1 + math.exp(min(starting_score, update_score) - max(starting_score, update_score)))
        self.save(skip_updated_at=True)

    def add_view(self):
        self.views += 1
        # the value used to view_increase starting_score per click
        update_score = Tile.popularity_devalue_rate * self.days_since_creation()
        starting_score = self.view_starting_score
        self.view_starting_score = max(starting_score, update_score) + math.log(
            1 + math.exp(min(starting_score, update_score) - max(starting_score, update_score)))
        self.save(skip_updated_at=True)

    def click_score(self):
        # returns the score of the tile based on the starting_score and how long ago the tile was created
        return math.exp(self.click_starting_score - Tile.popularity_devalue_rate *
                        self.days_since_creation())
    click_score.short_description = 'Click Score'

    def view_score(self):
        # returns the score of the tile based on the starting_score and how long ago the tile was created
        return math.exp(self.view_starting_score - Tile.popularity_devalue_rate *
                        self.days_since_creation())
    view_score.short_description = 'View Score'

    def log_score(self, score):
        # returns the log of a score with the smallest value being 1
        # makes sure that small scores do not get large log values
        return math.log(score + (0 if score > 2 * Tile.ratio else (Tile.ratio - score / 2)), Tile.ratio)

    def click_log_score(self):
        score = self.click_score()
        return self.log_score(score)

    def view_log_score(self):
        score = self.view_score()
        return self.log_score(score)

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

    def get_related(self):
        return TileRelation.get_related_tiles([self.id])


class TileRelation(BaseModel):
    tile_a = models.ForeignKey(Tile, related_name='+')
    tile_b = models.ForeignKey(Tile, related_name='+')

    # used to calculate the score for a relation
    # a bigger starting_score value does not necessarily mean a bigger score
    starting_score = models.FloatField(default=0.0)

    # variable used for popularity, the bigger the value, the faster popularity de-values
    popularity_devalue_rate = 0.15

    def clean(self):
        if self.tile_a_id > self.tile_b_id:
            self.tile_a_id, self.tile_b_id = self.tile_b_id, self.tile_a_id

    @classmethod
    def relate(cls, tile_a, tile_b):
        """updates the starting_score of relation"""

        id_a = tile_a.id
        id_b = tile_b.id
        related_tile, _ = cls.objects.get_or_create(tile_a_id=id_a, tile_b_id=id_b)
        update_score = TileRelation.popularity_devalue_rate * related_tile.days_since_creation()
        starting_score = related_tile.starting_score
        related_tile.starting_score = max(starting_score, update_score) + math.log(
            1 + math.exp(min(starting_score, update_score) - max(starting_score, update_score)))
        related_tile.save()
        return related_tile

    @classmethod
    def get_related_tiles(cls, tile_list):
        """returns a list of tiles related to the given tile list in order of popularity"""

        id_list = [tile.id for tile in tile_list]

        related_tiles = list(cls.objects.filter(Q(tile_a_id__in=id_list) | Q(tile_b_id__in=id_list)).exclude(tile_a_id__in=id_list, tile_b_id__in=id_list).select_related())
        related_tiles = sorted(related_tiles, key=lambda related_tile: related_tile.score(), reverse=True)
        tiles = []
        for related_tile in related_tiles:
            if related_tile.tile_a.id in id_list:
                tiles.append(related_tile.tile_b)
            else:
                tiles.append(related_tile.tile_a)
        return tiles


    def score(self):
        # returns the score of the tile based on the starting_score and how long ago the tile was created
        return math.exp(self.starting_score - TileRelation.popularity_devalue_rate * self.days_since_creation())
    score.short_description = 'Score'

    def log_score(self):
        # the lower the ratio, the bigger the range between low and high scores
        ratio = 1.5
        score = self.score()
        # returns the log of a score with the smallest value returned being 1
        # makes sure that small scores do not get large log values
        return math.log(score + (0 if score > 2 * ratio else(ratio - score / 2)), ratio)
