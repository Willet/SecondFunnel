from django_extensions.db.fields import UUIDField
import re
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from social_auth.db.django_models import UserSocialAuth

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

    # Django templates
    page = models.TextField(default=DEFAULT_PAGE, verbose_name='Page')

    # JS Templates
    # Main block templates
    shop_the_look = models.TextField(
        default=DEFAULT_SHOP_THE_LOOK,
        verbose_name='"Shop the look"'
    )
    featured_product = models.TextField(
        default=DEFAULT_FEATURED_PRODUCT,
        verbose_name='"Featured product"'
    )

    # Discovery block templates
    product = models.TextField(
        default=DEFAULT_PRODUCT,
        verbose_name='Product'
    )
    combobox = models.TextField(
        default=DEFAULT_COMBOBOX,
        verbose_name='Combobox'
    )
    youtube = models.TextField(
        default=DEFAULT_YOUTUBE,
        verbose_name='Youtube'
    )
    instagram = models.TextField(
        default=DEFAULT_INSTAGRAM,
        verbose_name='Image'
    )

    # Preview Templates
    product_preview = models.TextField(
        default=DEFAULT_PRODUCT_PREVIEW,
        verbose_name='Product preview'
    )
    combobox_preview = models.TextField(
        default=DEFAULT_COMBOBOX_PREVIEW,
        verbose_name='Combobox preview'
    )
    instagram_preview = models.TextField(
        default=DEFAULT_INSTAGRAM_PREVIEW,
        verbose_name='Image preview'
    )
    instagram_product_preview = models.TextField(
        default=DEFAULT_INSTAGRAM_PRODUCT_PREVIEW,
        verbose_name='Image product preview'
    )

    def __init__(self, *args, **kwargs):
        super(StoreTheme, self).__init__(*args, **kwargs)
        # Required is a bit of a misnomer...
        self.REQUIRED_FIELDS = {
            'opengraph_tags': {
                'type': 'template',
                'values': [
                    'pinpoint/campaign_opengraph_tags.html'
                ]
            },
            'header_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_head.html']
            },
            'desktop_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_scripts_core.html',
                        'pinpoint/campaign_scripts_desktop.html',
                        'pinpoint/default_templates.html']
            },
            'mobile_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_scripts_core.html',
                        'pinpoint/campaign_scripts_mobile.html']
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
        return u"Theme: %s" % self.name


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

class IntentRankCampaign(BaseModelNamed):
    def __unicode__(self):
        return u'{0}'.format(self.name)


class Campaign(BaseModelNamed):
    """
    Defines a pinpoint page.

    @ivar store: The store this page is for.
    @ivar content_blocks: The featured content blocks for this page.
    @ivar discovery_blocks: The discovery blocks for this page.
    @ivar live: Whether or not the current page is live.
    """
    store = models.ForeignKey(Store)
    theme = models.OneToOneField(StoreTheme,
        related_name='theme',
        blank=True,
        null=True,
        verbose_name='Campaign Theme')
    mobile = models.OneToOneField(StoreTheme,
        related_name='mobile',
        blank=True,
        null=True,
        verbose_name='Campaign Mobile Theme')
    content_blocks = models.ManyToManyField(BlockContent,
        related_name="content_campaign")

    discovery_blocks = models.ManyToManyField(
        BlockContent, related_name="discovery_campaign", blank=True, null=True)

    live = models.BooleanField(default=True)
    supports_categories = models.BooleanField(default=False)

    default_intentrank = models.ForeignKey(IntentRankCampaign,
        related_name='campaign', blank=True, null=True)
    intentrank = models.ManyToManyField(IntentRankCampaign,
        related_name='campaigns', blank=True, null=True)

    def __unicode__(self):
        return u"Campaign: %s" % self.name

    def save(self, *args, **kwargs):
        super(Campaign, self).save(*args, **kwargs)

        if not self.default_intentrank:
            if re.search(r'native shoes', self.store.name, re.I):
                ir_campaign = IntentRankCampaign.objects.get(
                    name='NATIVE SHOES COMMUNITY LOOKBOOK #066'
                )
            else:
                ir_campaign = IntentRankCampaign(
                    name=self.name,
                    slug=self.slug,
                    description=self.description
                )
                ir_campaign.save()

            self.default_intentrank = ir_campaign
            self.intentrank.add(ir_campaign)

    def get_theme(self, type):
        """Returns the best match for the given theme type.

        type: a string; either 'full' or 'mobile'
        """
        priorities = {
            'full'  : [
                self.theme,
                self.store.theme,
                None
            ],
            'mobile': [
                self.mobile,
                self.store.mobile,
                self.theme,
                self.store.theme,
                None
            ]
        }

        themes = priorities.get(type)
        if not themes:
            return None

        results = filter(None, themes)
        if not results:
            return None

        return results[0]


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
    
    def get_image(self, url=False):
        """
        Get an image associated with this block. Prefer custom image over existing image.
        
        @return: A Generic Image object.
        """
        
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

    # existing_image is populated if the campaign was created using
    # an image already in the database
    existing_image = models.ForeignKey(ProductMedia, blank=True, null=True)

    # custom_image is populated if the campaign was created using
    # an image already in the database
    custom_image   = models.OneToOneField(GenericImage, blank=True, null=True)

    existing_ls_image = models.ForeignKey(
        ProductMedia, blank=True, null=True, related_name='ls_image_set')
    custom_ls_image = models.OneToOneField(
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
        if not (self.existing_ls_image or self.custom_ls_image):
            raise ValidationError('Block needs at least one STL image.')
