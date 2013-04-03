import re
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from social_auth.db.django_models import UserSocialAuth

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
        <!--
        This statement is required; it loads any content needed for the
        head, and must be located in the <head> tag
        -->
        {{ header_content }}

    </head>
    <body>
        <!--This div will load the 'shop-the-look' template-->
        <div class="template target featured product" data-src="shop-the-look"></div>

        <!--This div will load the 'featured-product' template-->
        <div class="template target featured product" data-src="featured-product"></div>

        <div class='divider'>
            <div class='bar'></div>
            <span class='text'>Browse more</span>
        </div>
        <div class='discovery-area'></div>

        <!--
        This statement ensures that templates are available,
        and should come before {{body_content}}
        -->
        {{ js_templates }}

        <!--
        This statement loads any scripts that may be required. If you want to
        include your own javascript, include them after this statement
        -->
        {{ body_content }}
    </body>
</html>
    """

    DEFAULT_SHOP_THE_LOOK = """
<script type='text/template' data-template-id='shop-the-look'>
    <img src='<%= page["stl-image"] %>' />
    <img src='<%= page["featured-image"] %>' />
    <div><%= page.product.title %></b></div>
    <div><%= page.product.price %></div>
    <div><%= page.product.description %></div>
    <div>
    <% _.each(page.product.images, function(image){ %>
        <img src='<%= image %>'/>
    <% }); %>
    </div>
    <div>
        <% include social_buttons %>
    </div>
    <div>
        <a href='<%= page.product.url %>' target='_blank'>link</a>
    </div>
</script>
    """

    DEFAULT_FEATURED_PRODUCT = """
<script type='text/template' data-template-id='featured-product'>
    <img src='<%= page["featured-image"] %>' />
    <div><%= page.product.title %></b></div>
    <div><%= page.product.price %></div>
    <div><%= page.product.description %></div>
    <div>
    <% _.each(page.product.images, function(image){ %>
        <img src='<%= image %>'/>
    <% }); %>
    </div>
    <div>
        <% include social_buttons %>
    </div>
    <div>
        <a href='<%= page.product.url %>' target='_blank'>link</a>
    </div>
</script>
    """

    DEFAULT_PRODUCT = """
<script type='text/template' data-template-id='product'>
    <div class='block product'>
        <div><%= data.title %></div>
        <div><%= data.description %></div>
        <img src='<%= data.image %>'/>
        <div><%= data.url %></div>
        <% _.each(page.product.images, function(image){ %>
        <img src='<%= image %>'/>
        <% }); %>
    </div>
</script>
    """

    DEFAULT_COMBOBOX = """
<script type='text/template' data-template-id='combobox'>
    <div class='block product'>
        <img src='<%= data["lifestyle-image"] %>'/>
        <div><%= data.title %></div>
        <div><%= data.description %></div>
        <img src='<%= data.image %>'/>
        <div><%= data.url %></div>
        <% _.each(page.product.images, function(image){ %>
        <img src='<%= image %>'/>
        <% }); %>
    </div>
</script>
    """

    DEFAULT_YOUTUBE = """
<script type='text/template' data-template-id='youtube'>
    <% include youtube_video_template %>
</script>
    """

    DEFAULT_PRODUCT_PREVIEW = """
<script type='text/template' data-template-id='product-preview'>
    <div class='image'><img src='<%= data.image %>' /></div>
    <div class='images'>
        <% _.each(data.images, function(image) { %>
        <img src='<%= image %>' />
        <% }); %>
    </div>
    <div class='price'><%= data.price %></div>
    <div class='title'><%= data.title %></div>
    <div class='description'><%= data.description %></div>
    <div class='url'><a href='<%= data.url %>' target="_blank">BUY
        NOW</a></div>
    <% include social_buttons %>
    </div>
</script>
    """

    DEFAULT_COMBOBOX_PREVIEW = """
<script type='text/template' data-template-id='combobox-preview'>
    <div class='image'><img src='<%= data.image %>' /></div>
    <div class='images'>
        <% _.each(data.images, function(image) { %>
        <img src='<%= image %>' />
        <% }); %>
    </div>
    <div class='price'><%= data.price %></div>
    <div class='title'><%= data.title %></div>
    <div class='description'><%= data.description %></div>
    <div class='url'><a href='<%= data.url %>' target="_blank">BUY
        NOW</a></div>
    <% include social_buttons %>
    </div>
</script>
    """

    DEFAULT_INSTAGRAM_PREVIEW = """
<script type='text/template' data-template-id='instagram-preview'>
    <img src='<%= data["image"] %>'/>
</script>
    """

    DEFAULT_INSTAGRAM_PRODUCT_PREVIEW = """
<script type='text/template' data-template-id='instagram-product-preview'>
    <img src='<%= data["image"] %>'/>
</script>
    """

    DEFAULT_INSTAGRAM = """
<script type='text/template' data-template-id='instagram'
        data-appearance-probability='0.25'>
    <div class='block image external-content instagram'>
        <div class='product'>
            <div class='img-container'>
                <img src='<%= sizeImage(data.image, "master") %>'
                     alt='Instagram image'
                     data-original-id='<%= data["original-id"] %>' />
            </div>
        </div>
    </div>
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
    instagram = models.TextField(default=DEFAULT_INSTAGRAM)

    # Preview Templates
    product_preview = models.TextField(default=DEFAULT_PRODUCT_PREVIEW)
    combobox_preview = models.TextField(default=DEFAULT_COMBOBOX_PREVIEW)
    instagram_preview = models.TextField(default=DEFAULT_INSTAGRAM_PREVIEW)
    instagram_product_preview = models.TextField(
        default=DEFAULT_INSTAGRAM_PRODUCT_PREVIEW)



    def __init__(self, *args, **kwargs):
        super(StoreTheme, self).__init__(*args, **kwargs)
        self.REQUIRED_FIELDS = {
            'header_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_head.html']
            },
            'body_content': {
                'type': 'template',
                'values': ['pinpoint/default_templates.html',
                           'pinpoint/campaign_scripts.html']
            },
            'js_templates': {
                'type': 'theme',
                'values': [
                    # Featured area templates
                    'shop_the_look',
                    'featured_product',

                    # Discovery blocks
                    'product',
                    'combobox',
                    'youtube',
                    'instagram',

                    # Previews
                    'product_preview',
                    'combobox_preview',
                    'instagram_preview',
                    'instagram_product_preview'
                ]
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
        super(self.__class__, self).save(*args, **kwargs)

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