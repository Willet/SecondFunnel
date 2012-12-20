import re
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from apps.assets.models import (MediaBase, BaseModel, BaseModelNamed,
                                Store, GenericImage, Product, ProductMedia)


def page_template_includes(value):
    """
    Checks that the given template has its required fields.

    @param value: The template to check.

    @raise ValidationError: This is raised when a template is missing a required field.
    """
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
    """
    The database model for a store theme.

    @ivar DEFAULT_PAGE_TEMPLATE: The default page template.
    @ivar DEFAULT_FEATURED_PRODUCT: The default featured product block template.
    @ivar DEFAULT_PRODUCT_PREVIEW: The default template for the preview box content.
    @ivar DEFAULT_DISCOVERY_BLOCK: The default discovery block template.
    @ivar DEFAULT_YOUTUBE_BLOCK: The default youtube block template.

    @ivar store: A one-to-one foreign key to the store this template is for.
    @ivar page_template: The template for the entire page. Css is also usually put here.
    @ivar preview_product: The template for the content of the preview box.

    @ivar featured_product: The template for featured product blocks.

    @ivar discovery_product: The template for discovery blocks containing products.
    @ivar discovery_youtube: The template for discovery blocks containing youtube videos.
    """

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

    DEFAULT_YOUTUBE_BLOCK = """
    {% youtube_video video %}
    """

    # TODO: Replace with ForeignKey to support mobile themes?
    store = models.OneToOneField(Store, related_name="theme")
    page_template = models.TextField(default=DEFAULT_PAGE_TEMPLATE,
                                     validators=[page_template_includes])

    # Featured Content Templates
    featured_product = models.TextField(default=DEFAULT_FEATURED_PRODUCT)

    # Preview Templates
    preview_product = models.TextField(default=DEFAULT_PRODUCT_PREVIEW)

    # Discovery Block Templates
    discovery_product = models.TextField(default=DEFAULT_DISCOVERY_BLOCK)

    # Right now this is being hardcoded in, but should be changed to support
    # multiple block types automatically.

    # A system like the one Grigory had originally made, where block type slugs
    # mapped to templates, could be used here. Specifically, having a generic
    # block template model that has a one to one foreign key to both a store
    # and a block type.
    discovery_youtube = models.TextField(default=DEFAULT_YOUTUBE_BLOCK)

    def __unicode__(self):
        return u"Theme for Store: %s" % self.store


class StoreThemeMedia(MediaBase):
    theme = models.ForeignKey(StoreTheme, related_name="media")


class BlockType(BaseModelNamed):
    """
    Represents a type of content block.

    @ivar image: The image used to represent it in the admin ui.
    @ivar handler: The the name of the wizard to use when customizing
        this block type.
    @ivar enabled: Whether the block type is set up or not. This is used
        to show what we're working on.
    """
    image = models.FileField(
        "Wizard Image", upload_to="internal_images", blank=True, null=True)

    handler = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return u"Block type: %s" % self.name


class BlockContent(BaseModel):
    """
    Represents a generic content block. This allows other models to
    include content blocks without worrying what type of content they are.

    @ivar block_type: The type of content this is.
    @ivar priority:???
    @ivar content_type: The name of the model of the content block.
    @ivar object_id: The id of the model of type content_type.
    @ivar data: The generic foreign key that uses content_type and object_id
        to link to a content-type database object.
    """
    block_type = models.ForeignKey(BlockType)
    priority = models.IntegerField(blank=True, null=True)
    """@deprecated: This was never used."""

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    data = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u"BlockContent of type %s for %s" % (
            self.content_type, self.block_type
        )


class Campaign(BaseModelNamed):
    """
    Defines a pinpoint page.

    @ivar store: The store this page is for.
    @ivar content_blocks: The featured content blocks for this page.
    @ivar discovery_blocks: The discovery blocks for this page.
    @ivar live: Whether or not the current page is live.
    """
    store = models.ForeignKey(Store)
    content_blocks = models.ManyToManyField(
        BlockContent, related_name="content_campaign")

    discovery_blocks = models.ManyToManyField(
        BlockContent, related_name="discovery_campaign", blank=True, null=True)

    live = models.BooleanField(default=True)
    """@deprecated: Pinpoint pages are forever."""

    def __unicode__(self):
        return u"Campaign: %s" % self.name


class FeaturedProductBlock(BaseModelNamed):
    """
    Data model for Featured Content blocks, to be used with BlockContent

    @ivar product: The product to feature.
    @ivar existing_image: A scraped image to use to feature the
        product. Either this or custom_image must exist.
    @ivar custom_image: A custom image to use to feature the product.
        Either this or existing_image must exist.
    """

    product = models.ForeignKey(Product)
    existing_image = models.ForeignKey(ProductMedia, blank=True, null=True)
    custom_image = models.OneToOneField(GenericImage, blank=True, null=True)

    def __unicode__(self):
        return u"Featured Content Data for %s" % self.product

    def get_image(self):
        """
        Get an image associated with this block. Prefer custom image over existing image.

        @return: A Generic Image object.
        """

        return self.custom_image or self.existing_image or None


class ShopTheLookBlock(BaseModelNamed):
    """
    Data model for Shop the Look blocks, to be used with BlockContent.

    @attention: This should inherit from FeaturedProductBlock.

    @ivar product: The product to feature.
    @ivar existing_image: A scraped image to use to feature the
        product. Either this or custom_image must exist.
    @ivar custom_image: A custom image to use to feature the product.
        Either this or existing_image must exist.

    @ivar existing_ls_image: A scraped image to use to show the product
        in action. Either this or custom_image must exist.
    @ivar custom_ls_image: A custom image to use to show the product in
        action. Either this or existing_image must exist.
    """

    product = models.ForeignKey(Product)

    existing_image = models.ForeignKey(
        ProductMedia, blank=True, null=True)
    custom_image = models.OneToOneField(
        GenericImage, blank=True, null=True)

    existing_ls_image = models.ForeignKey(
        ProductMedia, blank=True, null=True, related_name='ls_image_set')
    custom_ls_image = models.OneToOneField(
        GenericImage, blank=True, null=True, related_name='ls_image')

    def __unicode__(self):
        return u"Featured Content Data for %s" % self.product

    def get_image(self):
        """Get an image associated with this block"""

        return self.custom_image or self.existing_image or None

    def get_ls_image(self):
        """Get a lifestyle image associated with this block"""

        return self.custom_ls_image or self.existing_ls_image or None
