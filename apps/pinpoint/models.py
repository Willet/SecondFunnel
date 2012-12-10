import re
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from apps.assets.models import (MediaBase, BaseModel, BaseModelNamed,
    Store, GenericImage, Product, ProductMedia)

def page_template_includes(value):
    # Ought to be a staticmethod, but can't for whatever reason...
    INCLUDE_PATTERN = re.compile('{{ *(\w*?) *}}')
    REQUIRED_FIELDS = ['featured_content', 'discovery_area',
                       'header_content', 'preview_area']

    matches = INCLUDE_PATTERN.findall(value)
    missing = []

    for field in REQUIRED_FIELDS:
        if not field in matches:
            missing.append(field)

    if missing:
        raise ValidationError('Missing required includes for page '
                              'template: {fields}'
        .format(fields=', '.join(missing)))

class StoreTheme(BaseModelNamed):
    DEFAULT_PAGE_TEMPLATE = """
    <!DOCTYPE HTML>
    <html>
        <head>
            {{ header_content }}
        </head>
        <body>
            <div class='page'>
                {{ featured_content }}
                {{ discovery_area }}
            </div>
            {{ preview_area }}
        </body>
    </html>
    """

    DEFAULT_FEATURED_PRODUCT = """
    <img src='{{ product.featured_image }}' />
    <p>Other images</p>
    <ul>
    {% if product.images|length > 1 %}
        {% for image in product.images %}
        <li>{{ image }}</li>
        {% endfor %}
    {% else %}
        <li>No other images</li>
    {% endif %}
    </ul>
    <div class='title'>{{ product.name }}</div>
    <div class='price'>{{ product.price }}</div>
    <div class='description'>{{ product.description }}</div>
    <div class='url'>{{ product.url }}</div>

    {% social_buttons product %}
    """

    DEFAULT_PRODUCT_PREVIEW = """
    <div class='title'></div>
    <div class='price'></div>
    <div class='description'></div>
    <div class='url'></div>
    <div class='image'></div>
    <div class='images'></div>
    <div class='social-buttons'></div>
    """

    DEFAULT_DISCOVERY_BLOCK = """
    <img src='{{ product.images.0 }}'/>
    <div>{{ product.name }}</div>
    {% social_buttons product %}
    <div style='display: none'>
        <!-- Testing -->
        <div class='price'>{{ product.price }}</div>
        <div class='description'>{{ product.description }}</div>
        <div class='url'>{{ product.url }}</div>
        <ul>
            {% for image in product.images %}
            <li>{{ image }}</li>
            {% endfor %}
        </ul>
    </div>
    """

    # TODO: Replace with ForeignKey to support mobile themes?
    store         = models.OneToOneField(Store, related_name="theme")
    page_template = models.TextField(default=DEFAULT_PAGE_TEMPLATE,
                                     validators=[page_template_includes])

    # Featured Content Templates
    featured_product  = models.TextField(default=DEFAULT_FEATURED_PRODUCT)

    # Preview Templates
    preview_product   = models.TextField(default=DEFAULT_PRODUCT_PREVIEW)

    # Discovery Block Templates
    discovery_product = models.TextField(default=DEFAULT_DISCOVERY_BLOCK)

    def __unicode__(self):
        return u"Theme for Store: %s" % self.store


class StoreThemeMedia(MediaBase):
    theme = models.ForeignKey(StoreTheme, related_name="media")


class BlockType(BaseModelNamed):
    image = models.FileField("Wizard Image",
        upload_to="internal_images", blank=True, null=True)

    handler = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return u"Block type: %s" % self.name


class BlockContent(BaseModel):
    block_type = models.ForeignKey(BlockType)
    priority = models.IntegerField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    data = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u"BlockContent of type %s for %s" % (
            self.content_type, self.block_type
        )


class Campaign(BaseModelNamed):
    store = models.ForeignKey(Store)
    content_blocks = models.ManyToManyField(BlockContent,
        related_name="content_campaign")

    discovery_blocks = models.ManyToManyField(BlockContent,
        related_name="discovery_campaign", blank=True, null=True)

    live = models.BooleanField(default=True)

    def __unicode__(self):
        return u"Campaign: %s" % self.name


class FeaturedProductBlock(BaseModelNamed):
    """Data model for Featured Content block, to be used with BlockContent"""

    product = models.ForeignKey(Product)
    existing_image = models.ForeignKey(ProductMedia, blank=True, null=True)
    custom_image = models.OneToOneField(GenericImage, blank=True, null=True)

    def __unicode__(self):
        return u"Featured Content Data for %s" % self.product

    def get_image(self):
        """Get an image associated with this block"""

        return self.custom_image or self.existing_image or None


class ShopTheLookBlock(BaseModelNamed):
    """Data model for Featured Content block, to be used with BlockContent"""

    product = models.ForeignKey(Product)

    existing_image = models.ForeignKey(
        ProductMedia, blank=True, null=True)
    custom_image   = models.OneToOneField(
        GenericImage, blank=True, null=True)

    existing_ls_image = models.ForeignKey(
        ProductMedia, blank=True, null=True, related_name='ls_image_set')
    custom_ls_image   = models.OneToOneField(
        GenericImage, blank=True, null=True, related_name='ls_image')

    def __unicode__(self):
        return u"Featured Content Data for %s" % self.product

    def get_image(self):
        """Get an image associated with this block"""

        return self.custom_image or self.existing_image or None

    def get_ls_image(self):
        """Get a lifestyle image associated with this block"""

        return self.custom_ls_image or self.existing_ls_image or None
