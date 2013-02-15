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
    DEFAULT_PAGE = """
    <!DOCTYPE HTML>
    <html>
        <head>
            {{ header_content }}
        </head>
        <body>
            {{ js_templates }}
            {{ body_content }}
        </body>
    </html>
    """

    DEFAULT_SHOP_THE_LOOK = """
    <script type='text/template' data-template-id='shop-the-look'>
    </script>
    """

    DEFAULT_FEATURED_PRODUCT = """
    <script type='text/template' data-template-id='featured-product'>
    </script>
    """

    DEFAULT_PRODUCT = """
    <script type='text/template' data-template-id='product'>
    </script>
    """

    DEFAULT_COMBOBOX = """
    <script type='text/template' data-template-id='combobox'>
    </script>
    """

    DEFAULT_YOUTUBE = """
    <script type='text/template' data-template-id='youtube'>
    </script>
    """

    DEFAULT_PREVIEW = """
    <script type='text/template' data-template-id='preview'>
    </script>
    """

    # TODO: Replace with ForeignKey to support mobile themes?
    store = models.OneToOneField(Store, related_name="theme")

    # Django templates
    page = models.TextField(default=DEFAULT_PAGE)

    # JS Templates
    # Main block templates
    shop_the_look = models.TextField(default=DEFAULT_SHOP_THE_LOOK)
    featured_product = models.TextField(default=DEFAULT_FEATURED_PRODUCT)

    # Discovery block templates
    product = models.TextField(default=DEFAULT_PRODUCT)
    combobox = models.TextField(default=DEFAULT_COMBOBOX)
    youtube = models.TextField(default=DEFAULT_YOUTUBE)

    # Preview Templates
    preview = models.TextField(default=DEFAULT_PREVIEW)

    def __init__(self, *args, **kwargs):
        super(StoreTheme, self).__init__(*args, **kwargs)
        self.REQUIRED_FIELDS = {
            'header_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_head.html']
            },
            'body_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_scripts.html']
            },
            'js_templates': {
                'type': 'theme',
                'values': ['shop_the_look', 'featured_product', 'product',
                           'combobox', 'youtube', 'preview']
            }
        }

    def __unicode__(self):
        return u"Theme: %s" % self.store


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
    """Holds a reference to a more specific block of content,
    such as "Featured product block" and "Shop the look block".
    """
    block_type = models.ForeignKey(BlockType)
    priority = models.IntegerField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    # This line was copied (and can be referenced) straight from
    # https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
    # It ties self.data with table(content_type)(pk=object_id).
    data = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u"BlockContent of type %s for %s: %s" % (
            self.content_type, self.block_type, self.data
        )

    def get_data(self):
        # tastypie patch
        return self.__unicode__()


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

    def get_image(self, url=False):
        """Get an image associated with this block"""

        image = self.custom_image or self.existing_image or None

        if url and image:
            return image.get_url()

        return image


    def save(self, *args, **kwargs):
        """Overridden save method to do multi-field validation."""
        self.clean()
        super(self.__class__, self).save(self, *args, **kwargs)

    def clean(self):
        """Multi-field validation goes here.

        docs.djangoproject.com/en/1.4/ref/models/instances/#validating-objects
        """
        if not (self.existing_image or self.custom_image):
            # TODO: "collect all the errors and return them all at once"
            #       (and display on the form, if model is being modified
            #        on a form)
            raise ValidationError('Block needs at least one product image.')


class ShopTheLookBlock(BaseModelNamed):
    """Data model for Featured Content block, to be used with BlockContent"""

    product = models.ForeignKey(Product)

    # existing_image is populated if the campaign was created using
    # an image already in the database
    existing_image = models.ForeignKey(ProductMedia, blank=True, null=True)

    # custom_image is populated if the campaign was created using
    # an image already in the database
    custom_image   = models.OneToOneField(GenericImage, blank=True, null=True)

    existing_ls_image = models.ForeignKey(
        ProductMedia, blank=True, null=True, related_name='ls_image_set')
    custom_ls_image   = models.OneToOneField(
        GenericImage, blank=True, null=True, related_name='ls_image')

    def __unicode__(self):
        return u"Featured Content Data for %s" % self.product

    def get_image(self, url=False):
        """Get an image associated with this block"""

        image = self.custom_image or self.existing_image or None

        if url and image:
            return image.get_url()

        return image

    def get_ls_image(self, url=False):
        """Get a lifestyle image associated with this block"""

        image = self.custom_ls_image or self.existing_ls_image or None

        if url and image:
            return image.get_url()

        return image

    def save(self, *args, **kwargs):
        """Overridden save method to do multi-field validation."""
        self.clean()
        super(self.__class__, self).save(self, *args, **kwargs)

    def clean(self):
        """Multi-field validation goes here.

        docs.djangoproject.com/en/1.4/ref/models/instances/#validating-objects
        """
        if not (self.existing_image or self.custom_image):
            # TODO: "collect all the errors and return them all at once"
            #       (and display on the form, if model is being modified
            #        on a form)
            raise ValidationError('Block needs at least one product image.')
        if not (self.existing_ls_image or self.custom_ls_image):
            raise ValidationError('Block needs at least one STL image.')