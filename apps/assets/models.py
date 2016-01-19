import calendar
from copy import deepcopy
import datetime
import decimal
import json
import logging
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.db import models, transaction
from django_extensions.db.fields import CreationDateTimeField
from jsonfield import JSONField
from model_utils.managers import InheritanceManager

import apps.api.serializers as cg_serializers
from apps.imageservice.fields import ImageSizesField
from apps.imageservice.models import ImageSizes
from apps.imageservice.utils import delete_resource, is_hex_color
import apps.intentrank.serializers as ir_serializers
from apps.utils.decorators import returns_unicode
from apps.utils.fields import ListField
from apps.utils.classes import MemcacheSetting

from .utils import delay_tile_serialization


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

    serializer = cg_serializer = cg_serializers.RawSerializer

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
                obj_name=getattr(self, 'name', '')).encode('ascii', 'ignore')

        return u'{class_name} #{obj_id}'.format(
            class_name=self.__class__.__name__,
            obj_id=self.pk).encode('ascii', 'ignore')

    @classmethod
    def _copy(cls, obj, update_fields=None, exclude_fields=None):
        """Copies fields over to new instance of class & saves it
        
        Note: related m2m fields not copied over by default! add to update_fields
        Note: Fields 'id' and 'ir_cache' are excluded by default
        Note: m2m field values can be a list of models, a django query <QuerySet>,
              or an existing m2m relation <RelatedManager>
        
        Warning: not tested with all related fields

        :param obj - instance to copy
        :param update_fields - dict of key,values of fields to update
        :param exclude_fields - list of field names to exclude from copying

        :return copied instance

        :raises: ValidationError
        """
        if update_fields is None:
            update_fields = {}
        if exclude_fields is None:
            exclude_fields = []
        # NOTE: _meta API updated in Django 1.8, will need to re-implement
        default_exclude = ['id', 'ir_cache']
        autofields = [f.name for f in obj._meta.fields if isinstance(f, models.AutoField)]
        exclude = list(set(exclude_fields + autofields + default_exclude)) # eliminate duplicates

        # local fields + many-to-many fields = all fields - related m2m fields
        local_fields = [f.name for f in obj._meta.local_fields]
        m2m_local_fields = [f.name for f in obj._meta.many_to_many]
        m2m_all_fields = list(set(obj._meta.get_all_field_names()) - set(local_fields)) # includes related_names

        # Remove excluded fields from fields that are copied
        local_kwargs = { k:getattr(obj,k) for k in local_fields if k not in exclude }
        # By default, skip copying of related relations
        m2m_kwargs = { k:getattr(obj,k) for k in m2m_local_fields if k not in exclude }

        # Separate update_fields into local & m2m
        local_update = { k:v for (k,v) in update_fields.iteritems() if k in local_fields }
        # Allow related relations to be copied if in update_fields
        m2m_update = { k:v for (k,v) in update_fields.iteritems() if k in m2m_all_fields }
        
        local_kwargs.update(local_update)
        m2m_kwargs.update(m2m_update)

        new_obj = cls(**local_kwargs)

        with transaction.atomic():
            with delay_tile_serialization():
                new_obj.get_pk()

                for (k,v) in m2m_kwargs.iteritems():
                    if isinstance(v,list) or isinstance(v, models.query.QuerySet):
                        setattr(new_obj, k, v)
                    elif callable(getattr(v, 'all', None)):
                        # assume this is a RelatedManager, can't check directly b/c generated at runtime
                        setattr(new_obj, k, v.all())
                    else:
                        raise TypeError("Value '{}' can't be assigned to \
                                         ManyToManyField '{}'".format(v, k))

                new_obj.save() # run full_clean to validate
        return new_obj

    def _replace_relations(self, others, exclude_fields=None):
        """
        Any relations pointing to `others` are replaced with `self`
        This is a core part of merging duplicate models

        :param others - list of objects to replace with self
        :param exclude_fields - list of field names to exclude from merging
        """
        if exclude_fields is None:
            exclude_fields = set()
        else:
            exclude_fields = set(exclude_fields)

        for obj in others:
            local_fields = set([f.name for f in obj._meta.local_fields])
            local_m2m_fields = set([f.name for f in obj._meta.many_to_many])
            all_fields = set(obj._meta.get_all_field_names())
            reverse_m2m_fields = list(all_fields - local_fields - local_m2m_fields
                                      - exclude_fields)

            # Move reverse many-to-many and reverse one-to-many relations to new model
            for field in reverse_m2m_fields:
                try:
                    for model in getattr(obj, field).all():
                        if model:
                            getattr(self, field).add(model)
                            getattr(obj, field).remove(model)
                except AttributeError:
                    # Likely has '_set' appended by default
                    field += "_set"
                    for model in getattr(obj, field).all():
                        if model:
                            getattr(self, field).add(model)
                            getattr(obj, field).remove(model)

    def update_ir_cache(self):
        """Generates and/or updates the IR cache for the current object.
        Remember to save object to persist!

        :returns (the cache, whether it was updated)
        """
        old_ir_cache = self.ir_cache
        self.ir_cache = ''  # force tile to regenerate itself

        try:
            new_ir_cache = self.to_str(skip_cache=True)
        except ir_serializers.SerializerError:
            new_ir_cache = ''
        
        if hasattr(self, 'placeholder'):
            self.placeholder = True if (len(new_ir_cache) == 0) else False

        self.ir_cache = new_ir_cache

        if new_ir_cache == old_ir_cache:
            return new_ir_cache, False
        else:
            return new_ir_cache, True

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

    def update_cg(self, other=None, **kwargs):
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
            logging.info(u"updated {0}.{1} to {2}".format(
                self, self._cg_attribute_name_to_python_attribute_name(key),
                other[key]))

        return self

    def save(self, *args, **kwargs):
        self.full_clean()

        if hasattr(self, 'pk') and self.pk:
            obj_key = "cg-{0}-{1}".format(self.__class__.__name__, self.id)
            MemcacheSetting.set(obj_key, None)  # save

        super(BaseModel, self).save(*args, **kwargs)

    def get_pk(self, *args, **kwargs):
        """
        Get pk for new model - required to set m2m fields on new instance
        
        This performs a save while skipping full_clean and ignoring any
        serialization errors that arise due to incomplete models.
        """
        try:
            super(BaseModel, self).save(*args, **kwargs)
        except ir_serializers.SerializerError:
            # ignore errors on serialization of incomplete model
            pass

    @property
    def cg_created_at(self):
        """(readonly) representation of the content graph timestamp"""
        return unicode(calendar.timegm(self.created_at.utctimetuple()) * 1000)

    @property
    def cg_updated_at(self):
        """(readonly) representation of the content graph timestamp"""
        return unicode(calendar.timegm(self.updated_at.utctimetuple()) * 1000)


class Store(BaseModel):
    """
    All other models exist under a store and should never be re-assigned.

    All other models under a store should cascade delete on store deletion
    """
    staff = models.ManyToManyField(User, related_name='stores')

    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    slug = models.CharField(max_length=64)
    display_out_of_stock = models.BooleanField(default=False)

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
    store = models.ForeignKey('Store', related_name='products', on_delete=models.CASCADE)
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
    # product_images  = <RelatedManager> ProductImages (many-to-one relationship)
    # tiles  = <RelatedManager> Tiles (many-to-many relationship)
    
    last_scraped_at = models.DateTimeField(blank=True, null=True)

    # keeps track of if/when a product is available but ran out
    in_stock = models.BooleanField(default=True)

    ## for custom, potential per-store additional fields
    ## for instance new-egg's egg-score; sale-prices; etc.
    # currently known used attrs:
    # - product_set
    attributes = JSONField(blank=True, null=True, default=lambda:{})

    similar_products = models.ManyToManyField('self', related_name='reverse_similar_products',
                                              symmetrical=False, null=True, blank=True)

    serializer = ir_serializers.ProductSerializer
    cg_serializer = cg_serializers.ProductSerializer

    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        if not self.attributes:
            self.attributes = {}

    def clean_fields(self, exclude=None):
        if exclude is None:
            exclude = []

        if not 'price' in exclude:
            if self.price and not (isinstance(self.price, decimal.Decimal) \
                or isinstance(self.price, float)):
                raise ValidationError({'price': [u'Product price must be decimal or float']})

            if self.sale_price and not (isinstance(self.sale_price, decimal.Decimal) \
                or isinstance(self.sale_price, float)):
                raise ValidationError({'sale_price': [u'Product sale price must be decimal or float']})

    def clean(self):
        if not self.attributes:
            self.attributes = {}

        # guarantee the default image is in the list of product images
        # (and vice versa)
        image_urls = [img.url for img in self.product_images.all()]
        if self.default_image and (self.default_image.url not in image_urls):
            # there is a default image and it's not in the list of product images
            self.product_images.add(self.default_image)
        elif not self.default_image and len(image_urls):
            # there is no default image
            self.default_image = self.product_images.first()

        if self.sale_price and self.sale_price > self.price:
            raise ValidationError({'sale_price': [u'Product sale price must be smaller than price']})

    def choose_lifestyle_shot_default_image(self):
        """Set a default_image that is not a product shot for the given tile"""
        if self.default_image and self.default_image != self.product_images.first():
            return
        for i, img in enumerate(self.product_images.all()):
            if not img.is_product_shot:
                # found a good image - make it the default & return
                self.default_image = img
                self.save()
                return
        # couldn't find a good image - just use the first one
        self.default_image = self.product_images.first()
        self.save()

    @property
    def is_placeholder(self):
        # A placeholder product is created by the scraper, starts with name 'placeholder'
        # and sku 'placeholder-{ semi-random hash }'
        return bool(self.name == 'placeholder' or 'placeholder' in self.sku)

    def merge(self, other_products):
        """
        Handles trickiness of replacing references to old products to the new one
        Deletes the other_products

        :param other_products - a list or QuerySet of <Product>s to replace relations with
        """
        if isinstance(other_products, Product):
            other_products = [other_products]
        for p in other_products:
            if self.store != p.store:
                raise ValueError('Can not merge products from different stores')
        
        self._replace_relations(other_products,
            exclude_fields=['product_images', 'similar_products'])
        for product in other_products:
            product.delete()

    @staticmethod
    def merge_products(products):
        """
        Merge products into most recent non-placeholder product

        products - <QuerySet> or list of <Product>'s

        returns: merged <Product>
        """
        # If products has 1 or None, return it stripped of the list container
        if len(products) < 2:
            return products[0] if len(products) else None

        not_placeholders = [p for p in products if not p.is_placeholder]
        # merge into the most recent not placehoder, or the first placeholder
        if not_placeholders:
            not_placeholders.sort(key=lambda p: p.created_at, reverse=True)
            product = not_placeholders[0]
            other_products = [p for p in products if p != product]
        else:
            # order doesnt matter with placeholders, take 1st one
            product = products.pop(0)
            other_products = products
        logging.info(u'Merging {} into {}'.format(other_products, product))
        product.merge(other_products)
        return product


class ProductImage(BaseModel):
    """An Image-like model class that is explicitly an image depicting
    a product, rather than any other kind.

    TODO: make it subclass of Image
    """
    product = models.ForeignKey('Product', related_name="product_images",
                                on_delete=models.CASCADE, blank=True, null=True,
                                default=None)

    url = models.TextField()  # store/.../.jpg
    original_url = models.TextField()  # gap.com/.jpg
    file_type = models.CharField(max_length=255, blank=True, null=True)
    file_checksum = models.CharField(max_length=512, blank=True, null=True)
    width = models.PositiveSmallIntegerField(blank=True, null=True)
    height = models.PositiveSmallIntegerField(blank=True, null=True)

    dominant_color = models.CharField(max_length=32, blank=True, null=True)
    image_sizes = ImageSizesField(blank=True, null=True)
    attributes = JSONField(blank=True, null=True, default=lambda:{})

    serializer = ir_serializers.ProductImageSerializer
    cg_serializer = cg_serializers.ProductImageSerializer

    class Meta(BaseModel.Meta):
        ordering = ('id', )

    def __init__(self, *args, **kwargs):
        # Convert image_sizes dict to ImageSizes
        if isinstance(kwargs.get('image_sizes', None), dict):
            image_sizes = kwargs['image_sizes']
            sizes = ImageSizes()
            for (name, size) in image_sizes.items():
                sizes[name] = size
            kwargs['image_sizes'] = sizes

        super(ProductImage, self).__init__(*args, **kwargs)
        if not self.attributes:
            self.attributes = {}

    @property
    def orientation(self):
        return "landscape" if self.width > self.height else "portrait"

    def save(self, *args, **kwargs):
        """self.image_sizes['master'] is populated by cloudinary
        """
        try:
            master_size = self.image_sizes['master']
        except KeyError:
            master_size = {
                'width': 0,
                'height': 0,
            }
        if not self.width:
            self.width = master_size['width']
        if not self.height:
            self.height = master_size['height']

        return super(ProductImage, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if settings.ENVIRONMENT == "production":
            # Delete stored image resources
            delete_resource(self.url)
            self.image_sizes.delete_resources()
        super(ProductImage, self).delete(*args, **kwargs)

    @property
    def is_product_shot(self):
        """The product_shot property."""
        product_shot = False
        if is_hex_color(self.dominant_color):
            red   = int("0x{}".format(self.dominant_color[1:3]), 0)
            blue  = int("0x{}".format(self.dominant_color[3:5]), 0)
            green = int("0x{}".format(self.dominant_color[5:7]), 0)
            threshold = 245
            if red > threshold and blue > threshold and green > threshold:
                product_shot = True
        return product_shot


class Tag(BaseModel):
    products = models.ManyToManyField('Product', related_name='tags')

    store = models.ForeignKey(Store, related_name='tags', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    url = models.TextField(blank=True, null=True)


class Content(BaseModel):
    def _validate_status(status):
        allowed = ["approved", "rejected", "needs-review"]
        if status not in allowed:
            raise ValidationError(
                _(u"{status} is not an allowed status; choices are {allowed}"),
                params={'status': status, 'allowed': allowed},
                code='invalid',
            )

    # Content.objects object for deserializing Content models as subclasses
    # Content.objects.select_subclasses() to get hetergenous instances
    # Content.objects.get_subclass(id=...) to get instance
    # Can also use .select_subclasses & .get_subclass on Content many-to-many fields
    # http://django-model-utils.readthedocs.org/en/latest/managers.html#inheritancemanager
    objects = InheritanceManager()

    store = models.ForeignKey('Store', related_name='content', on_delete=models.CASCADE)

    url = models.TextField()  # 2f.com/.jpg
    source = models.CharField(max_length=255)
    source_url = models.TextField(blank=True, null=True)  # gap/.jpg
    author = models.CharField(max_length=255, blank=True, null=True)

    tagged_products = models.ManyToManyField('Product', null=True, blank=True,
                                             related_name='content')
    # tiles = <RelatedManager> Tiles (many-to-many relationship)

    ## all other fields of proxied models will be store in this field
    ## this will allow arbitrary fields, querying all Content
    ## but restrict to only filtering/ordering on above fields
    attributes = JSONField(null=True, blank=True, default=lambda:{})

    # "approved", "rejected", "needs-review"
    status = models.CharField(max_length=255, blank=True, null=True,
                              default="needs-review",
                              validators=[_validate_status])

    _attribute_map = BaseModel._attribute_map + (
        # (cg attribute name, python attribute name)
        ('tagged-products', 'tagged_products'),
    )

    serializer = ir_serializers.ContentSerializer
    cg_serializer = cg_serializers.ContentSerializer

    def __init__(self, *args, **kwargs):
        super(Content, self).__init__(*args, **kwargs)
        if not self.attributes:
            self.attributes = {}
        if not self.source_url:
            self.source_url = self.url

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

        # WARNING THIS METHOD DOESN'T EXIST IN THE SUPERCLASS
        # Error: AttributeError: 'super' object has no attribute 'update'
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
        """attributes.sizes.master is populated by cloudinary
        """
        master_size = default_master_size
        try:
            master_size = self.attributes['sizes']['master']
        except KeyError:
            pass
        except TypeError:
            if isinstance(self.attributes, list):
                self.attributes = { "sizes": default_master_size }

        if master_size:
            self.width = master_size.get('width', 0)
            self.height = master_size.get('height', 0)
            logging.info(u"Setting {} width and height to {}x{}".format(self, self.width, self.height))

        return super(Image, self).save(*args, **kwargs)


    def delete(self, *args, **kwargs):
        if settings.ENVIRONMENT == "production":
            delete_resource(self.url)
        super(Image, self).delete(*args, **kwargs)


class Gif(Image):
    gif_url = models.TextField() # location of gif image

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
    # Store the image sizes to cache in S3
    # Size names are keys, with integer pixel values for width and height. None is acceptable
    # for either width or height, but no both.
    # example: {
    #               'w400': { 'width': 500, 'height': None, },
    #               'tile': { 'width': 700, 'height': 700, }
    #           }
    image_sizes = JSONField(blank=True, null=True, default=lambda:{})

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
            logging.info(u"speed up page load times by placing the theme \
                         '{0}' locally.".format(self.template))
            return remote_theme

        logging.warn(u"template '{0}' was neither local nor remote".format(
            self.template))
        return self.template


class Page(BaseModel):
    """
    Controls the source of the page content & how the page should look / behave

    Store -> Page -> Feed
    """
    store = models.ForeignKey('Store', related_name='pages', on_delete=models.CASCADE)
    name = models.CharField(max_length=256)  # e.g. Lived In
    theme = models.ForeignKey('Theme', related_name='pages', blank=True, null=True)
            #on_delete=models.SET_NULL,

    # attributes named differently
    theme_settings = JSONField(default=lambda:{}, blank=True, null=True)

    theme_settings_fields = [
        ('image_tile_wide', 0.0),
        ('desktop_hero_image', ''),
        ('mobile_hero_image', ''),
        ('column_width', 256),
        ('social_buttons', []),
        ('enable_tracking', "true"),
    ]

    dashboard_settings = JSONField(default=lambda:{}, blank=True)
    campaign = models.ForeignKey('dashboard.Campaign', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url_slug = models.CharField(max_length=128)  # e.g. livedin
    legal_copy = models.TextField(blank=True, null=True)
    last_published_at = models.DateTimeField(blank=True, null=True)
    feed = models.ForeignKey('Feed', related_name='page', blank=True, null=True) 
    # is_finite @property

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
        super(self.__class__, self).__init__(*args, **kwargs)
        # self._theme_settings is a merged theme_settings with defaults
        if not self.theme_settings:
            self._theme_settings = { key: default for (key, default)
                                     in self.theme_settings_fields }
        else:
            self._theme_settings = self.theme_settings.copy()
            for (key, default) in self.theme_settings_fields:
                if not key in self.theme_settings:
                    self._theme_settings[key] = default

    def __getattr__(self, name):
        try:
            # Need to use parent __getattribute__ to avoid infinite loop
            return super(self.__class__, self).__getattribute__('_theme_settings')[name]
        except (AttributeError, KeyError):
            return super(self.__class__, self).__getattribute__(name)

    def __copy__(self):
        """Duplicates the page, points to existing feed & associated tiles
        returns: page"""
        return self.__class__._copy(self,
                                    update_fields= {'url_slug': self._get_incremented_url_slug()})

    def __deepcopy__(self, memo={}):
        """Duplicates the page, feed & associated tiles
        returns: page"""
        feed = self.feed.deepcopy()
        feed.save() # ensure feed is saved
        return self.__class__._copy(self,
                                    update_fields= {'url_slug': self._get_incremented_url_slug(),
                                                    'feed': feed })

    def copy(self):
        """page.copy() is alias for copy(page)"""
        return self.__copy__()

    def deepcopy(self):
        """page.deepcopy() is alias for deepcopy(page)"""
        return self.__deepcopy__()

    def deepdelete(self):
        """Attempts to delete all database elements associated with this page iff
           those elements are not associated with any other page:
           - Feed (if only associated with this page)
           - Tiles (if associated with Feed)
           - Products (if only tagged in Tiles to be deleted)
           - Contents (if only tagged in Tiles to be deleted)

        :returns bool - True if deleted Feed & related items, False if only deleted Page
        """
        if not self.feed:
            self.delete()
            return False
        elif self.feed.page.count() > 1:
            # This Feed is associated with other pages, can't deep delete
            self.delete()
            return False
        else:
            # Get all product tiles & content tiles
            self.feed.deepdelete() # Will remove tiles too
            self.delete()
            return True

    def replace(self, page, deepdelete=False):
        """Replaces page with self (assuming its url_slug) & deletes page.  If the feed
        is only related to this page, it is deleted too.

        If deepdelete, then deepdelete page & feed.

        :returns bool - True if deleted Feed & related items, False if only deleted Page
        """
        self.url_slug = page.url_slug
        if deepdelete:
            return page.deepdelete()
        else:
            if page.feed.page.count() == 1:
                page.feed.delete()
            page.delete()
            return False
        self.save()

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

    @property
    def is_finite(self):
        return bool(self.feed.is_finite and
            not self.theme_settings.get('override_finite_feed', False))

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

    def _get_incremented_url_slug(self):
        """Returns the url_slug with an incremented number. Guaranteed unique url_slug
        - "url_slug_1" for "url_slug"
        - "url_slug_2" for "url_slug_1
        """
        def increment_url_slug(url_slug):
            m = re.match(r"^(.*_)(\d+)$", url_slug)
            if m:
                url_slug = m.group(1) + str(int(m.group(2)) + 1)
            else:
                url_slug += "_1"

            try:
                self.__class__.objects.get(store=self.store, url_slug=url_slug)
            except ObjectDoesNotExist:
                # url_slug unique
                pass
            else:
                # Recursively increment
                url_slug = increment_url_slug(url_slug)
            finally:
                return url_slug
        return increment_url_slug(self.url_slug)

    def _get_incremented_name(self):
        """Returns the name
        - "name COPY 1" for "name"
        - "name COPY 2" for "name COPY 1"
        """
        def increment_name(name):
            m = re.match(r"^(.* COPY )(\d+)$", name)
            if m:
                name = m.group(1) + str(int(m.group(2)) + 1)
            else:
                name += " COPY 1"

            try:
                self.__class__.objects.get(store=self.store, name=name)
            except ObjectDoesNotExist:
                # url_slug unique
                pass
            else:
                # Recursively increment
                name = increment_name(name)
            finally:
                return name
        return increment_name(self.name)

    def add(self, *args, **kwargs):
        """Alias for Page.feed.add
        """
        return self.feed.add(*args, **kwargs)

    def remove(self, *args, **kwargs):
        """Alias for Page.feed.remove
        """
        return self.feed.remove(*args, **kwargs)


class Feed(BaseModel):
    """
    Container for tiles for a page / ad

    Tiles are THE DEFINITION of what should exist in the feed, so be very careful
    about deleting tiles.  Hide tiles from a feed by toggling 'Placeholder' to True

    Start_url's are an instruction to the scraper about how to update *some* tiles

    Page -> Feed -> Tiles
    """
    # pages = <RelatedManager> Pages (many-to-one relationship)
    # tiles = <RelatedManager> Tiles (many-to-one relationship)
    store = models.ForeignKey('Store', related_name='feeds', on_delete=models.CASCADE)
    feed_algorithm = models.CharField(max_length=64, blank=True, null=True)  # ; e.g. magic, priority
    feed_ratio = models.DecimalField(max_digits=2, decimal_places=2, default=0.20,  # currently unused by any algo
                                     help_text="Percent of content to display on feed using ratio-based algorithm")
    is_finite = models.BooleanField(default=True)

    # Fields used as instructions to update need
    source_urls = ListField(blank=True, type=unicode) # List of urls feed is generated from, allowed to be empty
    spider_name = models.CharField(max_length=64, blank=True) # Spider defines behavior to update / regenerate page, '' valid

    serializer = ir_serializers.FeedSerializer

    def __unicode__(self):
        try:
            page_names = ', '.join(page.name for page in self.page.all())
            return u'Feed (#%s), pages: %s' % (self.id, page_names)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            return u'Feed (#%s)' % self.id
        except:
            return u'(Unsaved Feed)'

    def __copy__(self):
        """A shallow copy of a feed does not include tiles. It is highly unlikely that that
        was the intention.  Force conscious use of deepcopy
        """
        raise NotImplementedError

    def __deepcopy__(self, memo={}):
        """Creates a duplicate of the feed & its tiles
        :returns new feed"""
        feed = self.__class__._copy(self)
        for tile in self.tiles.all():
            feed._copy_tile(tile)
        return feed

    def deepcopy(self):
        """feed.deepcopy() is alias for deepcopy(feed)"""
        return self.__deepcopy__()

    def deepdelete(self):
        """Delete the feed, its tiles, and all product & content that is not
        tagged in any other tile"""
        self._deepdelete_tiles(self.tiles.select_related('products','content').all())
        self.delete() # Cascades to tiles

    def clear_category(self, category, deepdelete=False):
        """Delete all feed tiles tagged only with category

        :param tag - can be str (name field of category) or Category instance

        :option deepdelete - if True, delete all product & content that is not tagged
        in any other tile
        """
        category = category if isinstance(category, Category) else Category.objects.get(name=category)
        if deepdelete:
            tiles = self.tiles.select_related('products','content').filter(categories__in=[category])
            self._deepdelete_tiles(tiles)
        else:
            self.tiles.filter(categories__in=[category]).delete()

    def find_tiles(self, content=None, product=None):
        """:returns list of tiles with this product/content (if given)"""
        if content:
            return self.tiles.filter(content__id=content.id)
        elif product:
            return self.tiles.filter(products__id=product.id)
        else:
            return self.tiles.all()

    def get_in_stock_tiles(self):
        return self.tiles.exclude(products__in_stock=False)\
            .exclude(content__tagged_products__in_stock=False)

    def add(self, obj, priority=0, category=None, force_create_tile=False):
        """ Add a <Product>, <Content> as a new tile, or copy an existing <Tile> to the feed. If the
        Product already exists as a product tile, or the Content exists as a content tile, updates
        and returns that tile

        priority: <int>
        category: <Category> a new tile will be added to that category unless
                             a matching tile already exists in that category
        force_create_tile: <bool> if True, forces the creation of a new tile
                             in the category & with priority (always True for Tile's)

        :returns (<Tile>, <bool>) created

        :raises ValueError"""
        if isinstance(obj, Product):
            return self._add_product(product=obj, priority=priority, category=category,
                                     force_create_tile=force_create_tile)
        elif isinstance(obj, Content):
            return self._add_content(content=obj, priority=priority, category=category,
                                     force_create_tile=force_create_tile)
        elif isinstance(obj, Tile):
            tile = self._copy_tile(tile=obj, priority=priority, category=category)
            return (tile, True)
        raise ValueError("add() accepts either Product, Content or Tile; "
                         "got {}".format(obj.__class__))

    def remove(self, obj, deepdelete=False):
        """:raises ValueError"""
        if isinstance(obj, Product):
            return self._remove_product(product=obj, deepdelete=deepdelete)
        elif isinstance(obj, Content):
            return self._remove_content(content=obj, deepdelete=deepdelete)
        elif isinstance(obj, Tile):
            return (self._deepdelete_tiles(tiles=self.tiles.get(id=obj.id))
                   if deepdelete else obj.delete())
        raise ValueError("remove() accepts either Product, Content or Tile; "
                         "got {}".format(obj.__class__))

    @property
    def categories(self):
        """ Returns QuerySet of all categories tiles in this page belong to """
        return Category.objects.filter(tiles__in=self.tiles.all()).distinct()

    def get_all_products(self, pk_set=False, skip_similar_products=False, skip_tagged_products=False):
        """Gets all tagged, related & similar products to this feed. Useful for bulk updates

        pk_set (bool): if True, return a set of primary keys
        skip_similar_products (bool): if True, don't add product.similar_products
        skip_tagged_products (bool): if True, don't add content.tagged_products

        :returns <QuerySet> of products"""
        product_pks = set()

        # Get ALL the products associated with this page
        for tile in self.tiles.all():
            for product in tile.products.all():
                product_pks.add(product.pk)
                if not skip_similar_products and product.similar_products:
                    product_pks.update(product.similar_products.values_list('pk', flat=True))
            if not skip_tagged_products:
                for content in tile.content.all():
                    if content.tagged_products:
                        product_pks.update(content.tagged_products.values_list('pk', flat=True))
        if pk_set:
            return product_pks
        else:
            return Product.objects.filter(pk__in=product_pks).all()

    def _copy_tile(self, tile, priority=None, category=None):
        """Creates a copy of a tile to this feed

        :returns <Tile> copy"""
        update_fields = {
            'feed': self,
            'priority': priority if not None else tile.priority,
        }
        if category:
            update_fields['categories'] = [category]
        new_tile = tile._copy(update_fields=update_fields) # generates ir_cache

        return new_tile

    def _deepdelete_tiles(self, tiles):
        """Tiles is a <QuerySet> (ex: Feed.tiles.objects.all())

        TODO: incorporate tagged products & similar products"""
        tiles_set = set(tiles.values_list('pk', flat=True))
        bulk_delete_products = []
        bulk_delete_content = []

        for tile in tiles:
            # Queue products & content for deletion if they are ONLY tagged in
            # Tiles that will be delete
            for p in tile.products.all():
                if set(p.tiles.values_list('pk', flat=True)).issubset(tiles_set):
                    bulk_delete_products.append(p.pk)
            for c in tile.content.all():
                if set(c.tiles.values_list('pk', flat=True)).issubset(tiles_set):
                    bulk_delete_content.append(c.pk)

        Product.objects.filter(pk__in=bulk_delete_products).delete()
        Content.objects.filter(pk__in=bulk_delete_content).delete()

        tiles.delete()

    def _add_product(self, product, priority=0, category=None, force_create_tile=False):
        """Adds (if not present) a tile with this product to the feed.

        If force_create_tile is True, will create a new tile even an existing product tile exists

        :returns tuple (the tile, the product, whether it was newly added)
        :raises AttributeError, ValidationError
        """
        if not force_create_tile:
            # Check for existing tile
            query = models.Q(products__id=product.id, template='product')
            if category:
                query &= models.Q(categories__id=category.id)
            existing_tiles = self.tiles.filter(query)
            if len(existing_tiles):
                tile = existing_tiles[0]
                tile.priority = priority
                tile.save() # Update IR Cache
                logging.info(u"<Product {0}> already in the feed. \
                              Updated <Tile {1}>.".format(product.id, tile.id))
                return (tile, False)
        
        # create new tile
        with transaction.atomic():
            with delay_tile_serialization():
                new_tile = Tile(feed=self, template='product', priority=priority)
                new_tile.placeholder = product.is_placeholder
                new_tile.get_pk()
                new_tile.products.add(product)
                new_tile.save() # full clean & generate ir_cache

        if category:
            category.tiles.add(new_tile)
        logging.info(u"<Product {0}> added to the feed in \
                      <Tile {1}>.".format(product.id, new_tile.id))

        return (new_tile, True)

    def _add_content(self, content, priority=0, category=None, force_create_tile=False):
        """Adds (if not present) a tile with this content to the feed.

        If force_create_tile is True, will create a new tile even an existing content tile exists

        :returns tuple (the tile, the content, whether it was newly added)
        :raises AttributeError, ValidationError
        """
        if not force_create_tile:
            # Check for existing tile
            query = models.Q(content__id=content.id)
            if category:
                query &= models.Q(categories__id=category.id)
            existing_tiles = self.tiles.filter(query)
            if len(existing_tiles):
                # Update tile
                # Could attempt to be smarter about choosing the most appropriate tile to update
                # It would have just the 1 piece of content
                tile = existing_tiles[0]
                tile.priority = priority
                product_qs = content.tagged_products.all()
                tile.products.add(*product_qs)
                tile.save()
                logging.info(u"<Content {0}> already in the feed. Updated \
                              <Tile {1}>".format(content.id, tile.id))
                return (tile, False)

        # Create new tile
        if isinstance(content, Video):
            if 'youtube' in content.url:
                template = 'youtube'
            else:
                template = 'video'
        else:
            template = 'image'
        with transaction.atomic():
            with delay_tile_serialization():
                new_tile = Tile(feed=self, template=template, priority=priority)
                new_tile.get_pk()
                new_tile.content.add(content)
                product_qs = content.tagged_products.all()
                new_tile.products.add(*product_qs)
                new_tile.save() # full clean & generate ir_cache
        if category:
            category.tiles.add(new_tile)
        logging.info(u"<Content {0}> added to the feed. Created \
                      <Tile {1}>".format(content.id, new_tile.id))
        return (new_tile, True)

    def _remove_product(self, product, deepdelete=False):
        """Removes (if present) product tiles with this product from the feed.

        If deepdelete, product will be deleted too (wiping tagging associations)

        :raises AttributeError
        """
        tiles = self.tiles.filter(products__id=product.id, template='product')
        self._deepdelete_tiles(tiles) if deepdelete else tiles.delete()

    def _remove_content(self, content, deepdelete=False):
        """Removes (if present) tiles with this content from the feed that
        belongs to this page.

        If deepdelete, tries to delete other products & content associated with
        this content (will not delete them if they are in other tiles.

        :raises AttributeError
        """
        tiles = self.tiles.filter(content__id=content.id)
        self._deepdelete_tiles(tiles) if deepdelete else tiles.delete()

    def healthcheck(self):
        num_tiles_total = self.tiles.count()
        num_tiles_in_stock = self.tiles.filter(in_stock=True, placeholder=False).count()
        num_tiles_out_stock = self.tiles.filter(in_stock=False, placeholder=False).count()
        
        percent = num_tiles_in_stock/float(num_tiles_total)

        status = ""
        status_message = []

        if num_tiles_in_stock < 10:
            status = "ERROR"
            status_message.append("In-stock count < 10")
        if percent < 0.1:
            if status != "ERROR":
                status = "ERROR"
            status_message.append("In-stock count < 10%")
        elif status != "ERROR":
            if percent <= 0.3: 
                status = "WARNING"
                status_message.append("In-stock count is between 10% and 30%")
            else:
                status = "OK"
                status_message.append("In-stock count is greater than 30%")

        for cat in self.categories:
            num_tiles_total = cat.tiles.filter(in_stock=True, placeholder=False).count()
            if (num_tiles_total < 10):
                if status != "ERROR":
                    status = "ERROR"
                    status_message = []
                status_message.append(u"Category '{}' only has {} in-stock tiles".format(cat.name, num_tiles_total))
        
        status_message = "\n".join(status_message)
        # Results output
        results_message = {
            "in_stock": num_tiles_in_stock,
            "out_of_stock": num_tiles_out_stock,
            "placeholder": self.tiles.filter(placeholder=True).count()
        }

        return {
            "status": (status, status_message),
            "results": results_message
        }


class Category(BaseModel):
    """ Feed category, shared name across all feeds for a store

    Store -> Category -> Tiles

    # To filter a feed by category:
    category_tiles = Feed.tiles.objects.filter(categories__id=category)

    # To add tiles to a category, filter with the Store
    Category.objects.get(name=cat_name, store=store)
    """
    tiles = models.ManyToManyField('Tile', related_name='categories')
    store = models.ForeignKey('Store', related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    url = models.TextField(blank=True, null=True)

    def clean_fields(self, exclude=None):
        if exclude is None:
            exclude = []

        if not 'name' in exclude:
            kwargs = {
                'store': self.store,
                'name__iexact': self.name, # django field lookup "iexact", meaning: ignore case
            }
            # Make sure there aren't multiple Category's with the same name for this store
            try:
                cat = Category.objects.get(**kwargs)
            except Category.DoesNotExist:
                # First of its kind, ok
                pass
            except Category.MultipleObjectsReturned:
                # Already multiples, bail!
                raise ValidationError({'name': [u"Category's must have a \
                                                  unique name for each store"]})
            else:
                # Only one, make it sure its this one
                if not self.pk == cat.pk:
                    raise ValidationError({'name': [u"Category's must have a \
                                                      unique name for each store"]})


class Tile(BaseModel):
    """
    A unit in a feed, defined by a template, product(s) and content(s)

    In general, tiles should be created by the feed (add, copy)

    ir_cache is updated with every tile save.  See tile_saved task

    Feed -> Tile -> Products / Content
    """
    # <Feed>.tiles.all() gives you... all its tiles
    feed = models.ForeignKey('Feed', related_name='tiles', on_delete=models.CASCADE)
    # Universal templates: 'product', 'image', 'banner', 'youtube'
    # Invent templates as needed
    template = models.CharField(max_length=128)
    products = models.ManyToManyField('Product', blank=True, null=True,
                                      related_name='tiles')
    # use content.select_subclasses() instead of content.all()!
    content = models.ManyToManyField('Content', blank=True, null=True,
                                     related_name='tiles')
    # categories = <RelatedManager> Category (many-to-one relationship)

    # Tiles are sorted using this attribute
    #   - negative values are allowed.
    #   - identical values are randomly ordered.
    priority = models.IntegerField(null=True, default=0)
    clicks = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    # A placeholder tile is failing serialization (usually b/c its content and product are
    # failing serialization, or its missing necessary product/content for its tile template
    # Placeholders are hidden by IntentRank default
    placeholder = models.BooleanField(default=False)
    # Clean toggles in / out of stock
    in_stock = models.BooleanField(default=True)

    # miscellaneous attributes, e.g. "is_banner_tile"
    attributes = JSONField(blank=True, null=True, default=lambda:{})

    cg_serializer = cg_serializers.TileSerializer

    def _copy(self, *args, **kwargs):
        update_fields = kwargs.pop('update_fields', {})

        # Should only be able to copy if new feed & feed belong to same store
        if 'feed' in update_fields and not self.feed.store == update_fields['feed'].store:
            raise ValueError("Can not copy tile to feed belonging to a different store")

        # Copy over categories unless overridden
        if not 'categories' in update_fields:
            update_fields['categories'] = self.categories

        kwargs['update_fields'] = update_fields

        return super(Tile, self)._copy(self, *args, **kwargs)

    def clean_fields(self, exclude=None):
        if exclude is None:
            exclude = []

        # TODO: move m2m validation into a pre-save signal (see tasks.py)
        # If the tile has been saved before, validate its m2m relations
        if self.pk:
            if not 'products' in exclude and \
                    self.products.exclude(store__id=self.feed.store.id).count():
                raise ValidationError({'products': [u'Products may not be from a different store']})
            if not 'content' in exclude and \
                    self.content.exclude(store__id=self.feed.store.id).count():
                raise ValidationError({'content': [u'Content may not be from a different store']})

    def clean(self):
        if self.pk:
            products_stock_status = [bool(p.in_stock and not p.is_placeholder) \
                                     for p in self.products.all()]
            for content in self.content.all():
                products_stock_status += [bool(p.in_stock and not p.is_placeholder) \
                                          for p in content.tagged_products.all()]
            if not len(products_stock_status):
                # This tile has no tagged products, default to in_stock = True
                # Example: banner tile
                self.in_stock = True
            else:
                self.in_stock = bool(True in products_stock_status)

    def deepdelete(self):
        bulk_delete_products = []
        bulk_delete_content = []

        # Queue products & content for deletion if they are ONLY tagged in
        # this single Tile
        for p in self.products.all():
            if p.tiles.count() == 1:
                bulk_delete_products.append(p.pk)
        for c in self.content.all():
            if c.tiles.count() == 1:
                bulk_delete_content.append(c.pk)
        Product.objects.filter(pk__in=bulk_delete_products).delete()
        Content.objects.filter(pk__in=bulk_delete_content).delete()

        self.delete()

    def to_json(self, skip_cache=False):
        return json.loads(self.to_str(skip_cache=skip_cache))

    def to_str(self, skip_cache=False):
        # determine what kind of tile this is
        serializer = None
        try:
            target_class = self.template.capitalize()
            serializer = getattr(ir_serializers,
                                 '{}TileSerializer'.format(target_class))
        except AttributeError:
            # cannot find e.g. 'Youtube'TileSerializer -- use default
            serializer = ir_serializers.DefaultTileSerializer
        
        return serializer().to_str([self], skip_cache=skip_cache)

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
        if self.pk:
            if self.products.count():
                return self.products.first()
            for content in self.content.all():
                if content.tagged_products.count():
                    return content.tagged_products.first()
        return None

    @property
    def separated_content(self):
        """ a <dict> of content indexed by class 'images', 'videos', 'reviews' """
        contents = self.content.select_subclasses()
        return {
            'images': [image for image in contents if isinstance(image, Image)],
            'videos': [video for video in contents if isinstance(video, Video)],
            'reviews': [review for review in contents if isinstance(review, Review)],
        }

    def get_first_content_of(self, cls):
        """
        returns first content of type cls in tile 
        raises LookupError if no content of type cls is found
        """
        contents = self.content.select_subclasses()
        try:
            return next(c for c in contents if isinstance(c, cls))
        except StopIteration:
            raise LookupError
