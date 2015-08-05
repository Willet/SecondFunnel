import decimal

from django.conf import settings
from django.db import models
from jsonfield import JSONField
from model_utils.managers import InheritanceManager

import apps.api.serializers as cg_serializers
import apps.intentrank.serializers as ir_serializers
from apps.imageservice.utils import delete_cloudinary_resource

#from .structure import Store # deferred to end of file
from .core import BaseModel, default_master_size

"""
Tag -> Product -> ProductImage
       Content ===> Image => Gif
               |"=> Video
               "==> Review
"""

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
    # product_images is an array of ProductImages (many-to-one relationship)
    # tiles is an array of Tiles (many-to-many relationship)
    
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

    def clean(self):
        if not self.attributes:
            self.attributes = {}

        if self.price and not (isinstance(self.price, decimal.Decimal) or isinstance(self.price, float)):
            raise ValidationError('Product price must be decimal or float')

        sale_price = self.get('sale_price', self.attributes.get('sale_price', float()))
        if sale_price and not (isinstance(sale_price, decimal.Decimal) or isinstance(sale_price, float)):
            raise ValidationError('Product sale price must be decimal or float')
        
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

    attributes = JSONField(blank=True, null=True, default=lambda:{})

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
        """attributes.sizes.master is populated by cloudinary
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


class Tag(BaseModel):
    products = models.ManyToManyField('Product', related_name='tags')

    store = models.ForeignKey('Store', related_name='tags', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    url = models.TextField(blank=True, null=True)


class Content(BaseModel):
    def _validate_status(status):
        allowed = ["approved", "rejected", "needs-review"]
        if status not in allowed:
            raise ValidationError("{0} is not an allowed status; "
                                  "choices are {1}".format(status, allowed))

    # Content.objects object for deserializing Content models as subclasses
    # use Content.objects.select_subclasses() instead of Content.objects.all()!
    # use content.select_subclasses() instead of content.all()!
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
        if not self.source_url:
            self.source_url = self.url

    class Meta(BaseModel.Meta):
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
        """attributes.sizes.master is populated by cloudinary
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
    product = models.ForeignKey('Product')
    body = models.TextField()


# Circular import
from .structure import Store
