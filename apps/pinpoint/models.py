from django.core.exceptions import ValidationError
import re
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from apps.assets.models import (MediaBase, BaseModel, BaseModelNamed,
    Store, GenericImage, Product, ProductMedia)

def page_template_includes(value):
    # Ought to be a staticmethod, but can't for whatever reason...
    INCLUDE_PATTERN = re.compile('{{ ?(\w*?) ?}}')
    REQUIRED_FIELDS = ['featured_content', 'discovery_area',
                       'header_content']

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
    <html>
        <head>
            {% include header_content %}
        </head>
        <body>
            {% include featured_content %}
            {% include discovery_area %}
        </body>
    </html>
    """

    # TODO: Replace with ForeignKey to support mobile themes?
    store         = models.OneToOneField(Store, related_name="theme")
    page_template = models.TextField(default=DEFAULT_PAGE_TEMPLATE,
                                     validators=[page_template_includes])

    # Featured Content Templates
    featured_product  = models.TextField(default="")

    # Preview Templates
    preview_product   = models.TextField(default="")

    # Discovery Block Templates
    discovery_product = models.TextField(default="")

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
