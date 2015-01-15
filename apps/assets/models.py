import calendar
import datetime
import json
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.db import models
from django_extensions.db.fields import CreationDateTimeField
from jsonfield import JSONField
from model_utils.managers import InheritanceManager

from apps.utils import returns_unicode
import apps.api.serializers as cg_serializers
import apps.intentrank.serializers as ir_serializers
from apps.imageservice.utils import delete_cloudinary_resource
from apps.utils.models import MemcacheSetting


default_master_size = {
    'master': {
        'width': '100%',
        'height': '100%',
    }
}


class SerializableMixin(object):
    """Provides to_json() and to_cg_json() methods for model instances.

    To implement specific json formats, override these methods.
    """

    serializer = ir_serializers.RawSerializer
    cg_serializer = cg_serializers.RawSerializer

    def to_json(self, skip_cache=False):
        """default method for all models to have a json representation."""
        if hasattr(self.serializer, 'dump'):
            return self.serializer.dump(self, skip_cache=skip_cache)
        return self.serializer().serialize(iter([self]))

    def to_str(self, skip_cache=False):
        return self.serializer().to_str([self], skip_cache=skip_cache)

    def to_cg_json(self):
        """serialize into CG model. This is an instance shorthand."""
        return self.cg_serializer.dump(self)


class BaseModel(models.Model, SerializableMixin):
    created_at = CreationDateTimeField()
    created_at.editable = True

    # To change this value, use model.save(skip_updated_at=True)
    updated_at = models.DateTimeField(auto_now=True)

    # used by IR to bypass frequent re/deserialization to shave off CPU time
    ir_cache = models.TextField(blank=True, null=True)

    # @override
    _attribute_map = (
        # (cg attribute name, python attribute name)
        ('created', 'created_at'),
        ('last-modified', 'updated_at'),
    )

    class Meta(object):
        abstract = True

    def __getitem__(self, key):
        return getattr(self, key, None)

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

    def _cg_attribute_name_to_python_attribute_name(self, cg_attribute_name):
        """(method name can be shorter, but something about PEP 20)

        reads the model's key conversion map and returns whichever model
        attribute name it is that matches the given cg_attribute_name.

        :returns str
        """
        for cg_py in self._attribute_map:
            if cg_py[0] == cg_attribute_name:
                return cg_py[1]
        return cg_attribute_name  # not found, assume identical

    def _python_attribute_name_to_cg_attribute_name(self, python_attribute_name):
        """(method name can be shorter, but something about PEP 20)

        reads the model's key conversion map and returns whichever model
        attribute name it is that matches the given python_attribute_name.

        :returns str
        """
        for cg_py in reversed(self._attribute_map):
            if cg_py[1] == python_attribute_name:
                return cg_py[0]
        return python_attribute_name  # not found, assume identical

    @classmethod
    def update_or_create(cls, defaults=None, **kwargs):
        """Like Model.objects.get_or_create, either gets, updates, or creates
        a model based on current state. Arguments are the same as the former.

        Examples:
        >>> Store.update_or_create(id=2, defaults={"id": 3})
        (<Store: Store object>, True, False)  # created
        >>> Store.update_or_create(id=2, defaults={"id": 3})
        (<Store: Store object>, False, False)  # found
        >>> Store.update_or_create(id=2, id=4)
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
            if key in self.attributes:
                return self.attributes.get(key, default)
        return default

    def update(self, other=None, **kwargs):
        """This is not <dict>.update().

        Setting attributes of non-model fields does not raise exceptions..

        :param {dict} other    overwrites matching attributes in self.
        :param {dict} kwargs   only if other is not supplied, use kwargs
                               as other.

        :returns self (<dict>.update() does not return anything)
        """
        if not other:
            other = kwargs

        if not other:
            return self

        for key in other:
            if key == 'created':
                self.created_at = datetime.datetime.fromtimestamp(
                    int(other[key]) / 1000)
            elif key in ['last-modified', 'modified']:
                self.updated_at = datetime.datetime.fromtimestamp(
                    int(other[key]) / 1000)
            else:
                setattr(self,
                        self._cg_attribute_name_to_python_attribute_name(key),
                        other[key])
            print u"updated {0}.{1} to {2}".format(
                self, self._cg_attribute_name_to_python_attribute_name(key),
                other[key])

        return self

    def save(self, *args, **kwargs):
        self.full_clean()

        if hasattr(self, 'pk') and self.pk:
            obj_key = "cg-{0}-{1}".format(self.__class__.__name__, self.id)
            MemcacheSetting.set(obj_key, None)  # save

        super(BaseModel, self).save(*args, **kwargs)

    @property
    def cg_created_at(self):
        """(readonly) representation of the content graph timestamp"""
        return unicode(calendar.timegm(self.created_at.utctimetuple()) * 1000)

    @property
    def cg_updated_at(self):
        """(readonly) representation of the content graph timestamp"""
        return unicode(calendar.timegm(self.updated_at.utctimetuple()) * 1000)


class Store(BaseModel):
    staff = models.ManyToManyField(User, related_name='stores')

    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    slug = models.CharField(max_length=64)

    default_theme = models.ForeignKey('Theme', related_name='store', blank=True,
                                      null=True, on_delete=models.SET_NULL)
    default_page = models.ForeignKey('Page', related_name='default_store', blank=True,
                                     null=True, on_delete=models.SET_NULL)

    public_base_url = models.URLField(
        help_text="e.g. http://explore.nativeshoes.com, used for store detection",
        blank=True, null=True)

    serializer = ir_serializers.StoreSerializer
    cg_serializer = cg_serializers.StoreSerializer

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
    store = models.ForeignKey(Store, related_name='products')
    name = models.CharField(max_length=1024, default="")
    description = models.TextField(blank=True, null=True, default="")
    # point form stuff like <li>hand wash</li> that isn't in the description already
    details = models.TextField(blank=True, null=True, default="")
    url = models.TextField()
    sku = models.CharField(max_length=255)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=5, default="$")

    default_image = models.ForeignKey('ProductImage', related_name='default_image',
                                      blank=True, null=True, on_delete=models.SET_NULL)
    # product_images is an array of ProductImages (many-to-one relationship)

    last_scraped_at = models.DateTimeField(blank=True, null=True)

    # keeps track of if/when a product is available but ran out
    in_stock = models.BooleanField(default=True)

    ## for custom, potential per-store additional fields
    ## for instance new-egg's egg-score; sale-prices; etc.
    # currently known used attrs:
    # - product_set
    attributes = JSONField(blank=True, null=True, default={})

    similar_products = models.ManyToManyField('self', related_name='reverse_similar_products', symmetrical=False, null=True, blank=True)

    serializer = ir_serializers.ProductSerializer
    cg_serializer = cg_serializers.ProductSerializer

    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        if not self.attributes:
            self.attributes = {}

    def clean(self):
        if not self.attributes:
            self.attributes = {}
        price_regex = re.compile(ur'C?(?:\$|\u20AC|\u20A3)\ ?(?:\d{1,3}(?:,\d{3})+|\d*)(?:\.\d{1,2})?')
        if self.price:
            match = re.match(price_regex, self.price)
            if not match:
                raise ValidationError('Product price does not validate')
        sale_price = self.attributes.get('sale_price', u'')
        if sale_price:
            match = re.match(price_regex, sale_price)
            if not match:
                raise ValidationError('Product sale price does not validate')

        # guarantee the default image is in the list of product images
        # (and vice versa)
        image_urls = [img.url for img in self.product_images.all()]
        if self.default_image and (self.default_image.url not in image_urls):
            # there is a default image and it's not in the list of product images
            self.product_images.add(self.default_image)
        elif not self.default_image and len(image_urls):
            # there is no default image
            self.default_image = self.product_images.all()[0]


class ProductImage(BaseModel):
    """An Image-like model class that is explicitly an image depicting
    a product, rather than any other kind.
    """
    product = models.ForeignKey(Product, related_name="product_images",
                                blank=True, null=True, default=None)

    url = models.TextField()  # store/.../.jpg
    original_url = models.TextField()  # gap.com/.jpg
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)
    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    dominant_color = models.CharField(max_length=32, blank=True, null=True)

    attributes = JSONField(blank=True, null=True, default={})

    serializer = ir_serializers.ProductImageSerializer
    cg_serializer = cg_serializers.ProductImageSerializer

    class Meta(BaseModel.Meta):
        ordering = ('id', )

    def image_tag(self):
        return u'<img src="%s" style="width: 400px;"/>' % self.url

    image_tag.allow_tags = True

    def __init__(self, *args, **kwargs):
        super(ProductImage, self).__init__(*args, **kwargs)
        if not self.attributes:
            self.attributes = {}

    @property
    def orientation(self):
        return "landscape" if self.width > self.height else "portrait"

    def save(self, *args, **kwargs):
        """For whatever reason, ProductImages have separate width and height
        attributes that are never populated by current code.
        """
        master_size = default_master_size
        try:
            master_size = self.attributes['sizes']['master']
        except KeyError:
            pass
        except TypeError:
            if isinstance(self.attributes, list):
                self.attributes = {"sizes": default_master_size}

        if master_size:
            self.width = master_size.get('width', 0)
            self.height = master_size.get('height', 0)

        return super(ProductImage, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if settings.ENVIRONMENT == "production" and settings.CLOUDINARY_BASE_URL in self.url:
            delete_cloudinary_resource(self.url)
        super(ProductImage, self).delete(*args, **kwargs)


class Category(BaseModel):
    products = models.ManyToManyField(Product, related_name='categories')

    store = models.ForeignKey(Store, related_name='categories')
    name = models.CharField(max_length=255)

    url = models.TextField(blank=True, null=True)


class Content(BaseModel):
    def _validate_status(status):
        allowed = ["approved", "rejected", "needs-review"]
        if status not in allowed:
            raise ValidationError("{0} is not an allowed status; "
                                  "choices are {1}".format(status, allowed))

    # Content.objects object for deserializing Content models as subclasses
    objects = InheritanceManager()

    store = models.ForeignKey(Store, related_name='content')

    url = models.TextField()  # 2f.com/.jpg
    source = models.CharField(max_length=255)
    source_url = models.TextField(blank=True, null=True)  # gap/.jpg
    author = models.CharField(max_length=255, blank=True, null=True)

    tagged_products = models.ManyToManyField(Product, null=True, blank=True,
                                             related_name='content')

    ## all other fields of proxied models will be store in this field
    ## this will allow arbitrary fields, querying all Content
    ## but restrict to only filtering/ordering on above fields
    attributes = JSONField(null=True, blank=True, default={})

    # "approved", "rejected", "needs-review"
    status = models.CharField(max_length=255, blank=True, null=True,
                              default="needs-review",
                              validators=[_validate_status])

    _attribute_map = BaseModel._attribute_map + (
        # (cg attribute name, python attribute name)
        ('tagged-products', 'tagged_products'),
        ('page-prioritized', 'deprecated_attribute?'),
    )

    serializer = ir_serializers.ContentSerializer
    cg_serializer = cg_serializers.ContentSerializer

    def image_tag(self):
        return u'<img src="%s" style="width: 400px;"/>' % self.url

    image_tag.allow_tags = True

    def __init__(self, *args, **kwargs):
        super(Content, self).__init__(*args, **kwargs)
        if not self.attributes:
            self.attributes = {}

    class Meta(object):
        verbose_name_plural = 'Content'

    def update(self, other=None, **kwargs):
        """Additional operations for converting tagged-products: [123] into
        actual tagged_products: [<Product>]s
        """
        if not other:
            other = kwargs

        if not other:
            return self

        if 'tagged-products' in other:
            other['tagged-products'] = [Product.objects.get(id=x) for x in
                                        other['tagged-products']]

        return super(Content, self).update(other=other)


class Image(Content):
    name = models.CharField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    original_url = models.TextField()
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)

    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    dominant_color = models.CharField(max_length=32, blank=True, null=True)

    serializer = ir_serializers.ImageSerializer
    cg_serializer = cg_serializers.ImageSerializer

    @property
    def orientation(self):
        return "landscape" if self.width > self.height else "portrait"

    def save(self, *args, **kwargs):
        """For whatever reason, Images have separate width and height
        attributes that are never populated by current code.
        """
        master_size = default_master_size
        try:
            master_size = self.attributes['sizes']['master']
        except KeyError:
            pass
        except TypeError:
            if isinstance(self.attributes, list):
                self.attributes = {"sizes": default_master_size}

        if master_size:
            self.width = master_size.get('width', 0)
            self.height = master_size.get('height', 0)
            print "Setting width and height to %dx%d" % (self.width, self.height)

        return super(Image, self).save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        if settings.ENVIRONMENT == "production" and settings.CLOUDINARY_BASE_URL in self.url:
            delete_cloudinary_resource(self.url)
        super(Image, self).delete(*args, **kwargs)


class Gif(Image):
    baseImageURL = models.TextField() # location of gif image

    serializer = ir_serializers.GifSerializer
    cg_serializer = cg_serializers.GifSerializer


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

    serializer = ir_serializers.VideoSerializer
    cg_serializer = cg_serializers.VideoSerializer


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
    template = models.CharField(
        max_length=1024,
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
        from apps.light.utils import read_a_file, read_remote_file

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
    feed_algorithm = models.CharField(max_length=64, blank=True, null=True)  # ; e.g. sorted, recommend
    feed_ratio = models.DecimalField(max_digits=2, decimal_places=2, default=0.20,  # currently only used by ir_mixed
                                     help_text="Percent of content to display on feed using ratio-based algorithm")
    is_finite = models.BooleanField(default=False)

    serializer = ir_serializers.FeedSerializer

    def __unicode__(self):
        try:
            page_names = ', '.join(page.name for page in self.page.all())
            return u'Feed (#%s), pages: %s' % (self.id, page_names)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return u'Feed (#%s)' % self.id
        except:
            return u'(Unsaved Feed)'

    def find_tiles(self, content=None, product=None):
        """:returns list of tiles with this product/content (if given)"""
        if content:
            tiles = self.tiles.filter(content__id=content.id)
        else:
            tiles = self.tiles.all()

        if not product:
            return tiles
        return tiles.filter(products__id=product.id)

    def get_in_stock_tiles(self):
        return self.tiles.exclude(products__in_stock=False)\
            .exclude(content__tagged_products__in_stock=False)

    def add(self, obj, prioritized=False, priority=0):
        """:raises ValueError"""
        if isinstance(obj, Product):
            return self._add_product(product=obj, prioritized=prioritized,
                                     priority=priority)
        elif isinstance(obj, Content):
            return self._add_content(content=obj, prioritized=prioritized,
                                     priority=priority)
        raise ValueError("add() accepts either Product or Content; "
                         "got {}".format(obj.__class__))

    def remove(self, obj):
        """:raises ValueError"""
        if isinstance(obj, Product):
            return self._remove_product(product=obj)
        elif isinstance(obj, Content):
            return self._remove_content(content=obj)
        raise ValueError("remove() accepts either Product or Content; "
                         "got {}".format(obj.__class__))

    def _add_product(self, product, prioritized=False, priority=0):
        """Adds (if not present) a tile with this product to the feed.

        This operation is so common and indirect that it is going
        to stay in models.py.

        TODO: can be faster

        :returns tuple (the tile, the product, whether it was newly added)
        :raises AttributeError
        """
        product_tiles = [tile for tile in self.tiles.all()
                         if tile.products.count() > 0]
        for tile in product_tiles:
            if product in tile.products.all():
                print "product {0} is already in the feed.".format(product.id)

                return tile, product, False
        else:  # there weren't any tiles with this product in them
            new_tile = Tile(feed=self,
                            template='product',
                            prioritized=prioritized,
                            priority=priority)

            new_tile.save()
            new_tile.products.add(product)
            print "product {0} added to the feed.".format(product.id)
            self.tiles.add(new_tile)

            return new_tile, product, True

    def _add_content(self, content, prioritized=False, priority=0):
        """Adds (if not present) a tile with this content to the feed.

        This operation is so common and indirect that it is going
        to stay in models.py.

        TODO: can be faster

        :returns tuple (the tile, the content, whether it was newly added)
        :raises AttributeError
        """
        content_tiles = [tile for tile in self.tiles.all()
                         if tile.content.count() > 0]
        for tile in content_tiles:
            if Tile.objects.filter(content=content).exists():
                print "content {0} already exists in feed".format(content.id)
                return tile, content, False

        else:  # there weren't any tiles with this content in them
            new_tile = Tile(feed=self,
                            template='image',
                            prioritized=prioritized,
                            priority=priority)

            # content template adjustments. should probably be somewhere else
            if isinstance(content, Video):
                if 'youtube' in content.url:
                    new_tile.template = 'youtube'
                else:
                    new_tile.template = 'video'

            new_tile.save()
            new_tile.content.add(content)
            print "content {0} added to the feed.".format(content.id)
            self.tiles.add(new_tile)

            return new_tile, content, True

    def _remove_product(self, product):
        """Removes (if present) tiles with this product from the feed that
        belongs to this page.

        This operation is so common and indirect that it is going
        to stay in models.py.

        TODO: can be faster

        :raises AttributeError
        """
        for tile in self.tiles.all():
            if tile.products.filter(id=product.id).exists():
                tile.delete()

    def _remove_content(self, content):
        """Removes (if present) tiles with this content from the feed that
        belongs to this page.

        This operation is so common and indirect that it is going
        to stay in models.py.

        TODO: can be faster

        :raises AttributeError
        """
        for tile in self.tiles.all():
            if tile.content.filter(id=content.id).exists():
                tile.delete()


class Page(BaseModel):
    store = models.ForeignKey(Store, related_name='pages')

    name = models.CharField(max_length=256)  # e.g. Lived In
    theme = models.ForeignKey(Theme, related_name='page', blank=True, null=True)

    # attributes named differently
    theme_settings = JSONField(blank=True, null=True)

    theme_settings_fields = [
        ('image_tile_wide', 0.0),
        ('desktop_hero_image', ''),
        ('mobile_hero_image', ''),
        ('column_width', 256),
        ('social_buttons', []),
        ('enable_tracking', "true"),
    ]

    dashboard_settings = JSONField(default={}, blank=True)
    campaign = models.ForeignKey('dashboard.Campaign', null=True, blank=True)

    description = models.TextField(blank=True, null=True)
    url_slug = models.CharField(max_length=128)  # e.g. livedin
    legal_copy = models.TextField(blank=True, null=True)

    last_published_at = models.DateTimeField(blank=True, null=True)

    feed = models.ForeignKey(Feed, related_name='page')

    _attribute_map = BaseModel._attribute_map + (
        # (cg attribute name, python attribute name)
        ('social-buttons', 'social_buttons'),
        ('column-width', 'column_width'),
        ('intentrank-id', 'intentrank_id'),
        ('heroImageDesktop', 'desktop_hero_image'),
        ('heroImageMobile', 'mobile_hero_image'),
        ('legalCopy', 'legal_copy'),  # ordered for cg -> sf
        ('description', 'description'),  # ordered for cg -> sf
        ('shareText', 'description'),  # ordered for cg <- sf
    )

    serializer = ir_serializers.PageSerializer
    cg_serializer = cg_serializers.PageSerializer

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        # self._theme_settings is a merged theme_settings with defaults
        if not self.theme_settings:
            self._theme_settings = { key: default for (key, default) in self.theme_settings_fields }
        else:
            self._theme_settings = self.theme_settings.copy()
            for (key, default) in self.theme_settings_fields:
                if not key in self.theme_settings:
                    self._theme_settings[key] = default

    def __getattr__(self, name):
        try:
            return self._theme_settings[name]
        except KeyError:
            return super(Page, self).__getattribute__(name)

    def get(self, key, default=None):
        """Duck-type a <dict>'s get() method to make CG transition easier.

        Also looks into the theme_settings JSONField if present.
        """
        try:
            return getattr(self, key)
        except AttributeError:
            pass

        if hasattr(self, 'theme_settings') and self.theme_settings:
            if key in self.theme_settings:
                return self.theme_settings.get(key, default)
        return default

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

    def add(self, obj, prioritized=False, priority=0):
        return self.feed.add(obj=obj, prioritized=prioritized,
                             priority=priority)

    def remove(self, obj):
        return self.feed.remove(obj=obj)


class Tile(BaseModel):
    def _validate_prioritized(status):
        allowed = ["", "request", "pageview", "session", "cookie", "custom"]
        if type(status) == bool:
            status = "pageview" if status else ""
        if status not in allowed:
            raise ValidationError("{0} is not an allowed status; "
                                  "choices are {1}".format(status, allowed))
        return status

    # <Feed>.tiles.all() gives you... all its tiles
    feed = models.ForeignKey(Feed, related_name='tiles')

    template = models.CharField(max_length=128)

    products = models.ManyToManyField(Product, blank=True, null=True,
                                      related_name='tiles')
    # use content.select_subclasses() instead of content.all()!
    content = models.ManyToManyField(Content, blank=True, null=True,
                                     related_name='tiles')

    # '': not prioritized.
    # 'request': prioritized for every IR request made by the client.
    # 'pageview': prioritized for every page view made by the client. (implemented in some algorithms, see docs)
    # 'session': prioritized for the beginning of each session.
    # 'cookie': prioritized if the tile cookie does not exist. (not implemented)
    # 'custom': run the tile's priority function that returns an int.
    #           the tile will be as prioritized within the feed as the size
    #           of that int. (not implemented)
    prioritized = models.CharField(
        max_length=255, default="", blank=True,
        null=True, validators=[_validate_prioritized])

    # if the feed's algorithm is 'generic', then priority is not used.
    # if the feed's algorithm is 'ordered', then prioritized tiles will be
    # sorted using this attribute instead of the tile's created date.
    #   negative values are allowed.
    #   identical values are shuffled.
    priority = models.IntegerField(null=True, default=0)

    # miscellaneous attributes, e.g. "is_banner_tile"
    attributes = JSONField(blank=True, null=True, default={})

    clicks = models.PositiveIntegerField(default=0)

    views = models.PositiveIntegerField(default=0)

    cg_serializer = cg_serializers.TileSerializer

    def full_clean(self, exclude=None, validate_unique=True):
        # south turns False into string 'false', which isn't what we wanted.
        # this turns 'true' and 'false' into appropriate priority flags.
        if type(self.prioritized) == bool:
            self.prioritized = 'pageview' if self.prioritized else ''
        if self.prioritized == 'true':
            self.prioritized = 'pageview'
        if self.prioritized in [0, '0', 'false']:
            self.prioritized = ''
        return super(Tile, self).full_clean(exclude=exclude,
                                            validate_unique=validate_unique)

    def to_json(self, skip_cache=False):
        return json.loads(self.to_str(skip_cache=skip_cache))

    def to_str(self, skip_cache=False):
        # determine what kind of tile this is
        serializer = None
        try:
            target_class = self.template.capitalize()
            serializer = getattr(ir_serializers,
                                 '{}TileSerializer'.format(target_class))
        except AttributeError:  # cannot find e.g. 'Youtube'TileSerializer -- use default
            pass

        if not serializer:  # default
            serializer = ir_serializers.TileSerializer

        return serializer().to_str([self], skip_cache=skip_cache)

    def update_ir_cache(self):
        """Generates and/or updates the IR cache for the current object.
        This method is generic; BaseModel might benefit later.

        :returns (the cache, whether it was updated)
        """
        old_ir_cache = self.ir_cache
        self.ir_cache = ''  # force tile to regenerate itself
        new_ir_cache = self.to_str(skip_cache=True)

        if new_ir_cache == old_ir_cache:
            return new_ir_cache, False

        self.ir_cache = new_ir_cache
        return new_ir_cache, True

    @property
    def tile_config(self):
        """(read-only) representation of the tile as its content graph
        tileconfig."""
        return cg_serializers.TileConfigSerializer.dump(self)

    @property
    def product(self):
        """Returns the tile's first product, or the first tagged product from
        the tile's first piece of content that has tagged products.
        """
        if self.products.count():
            return self.products.all()[0]
        for content in self.content.all():
            if content.tagged_products.count():
                return content.tagged_products.all()[0]

        return None
