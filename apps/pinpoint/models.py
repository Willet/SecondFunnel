from django_extensions.db.fields import UUIDField
import re
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from social_auth.db.django_models import UserSocialAuth

from apps.assets.models import (MediaBase, BaseModel, BaseModelNamed,
                                Store, GenericImage, Product, ProductMedia)


class StoreTheme(BaseModelNamed):
    """
    The database model for a store theme.

    @ivar DEFAULT_PAGE_TEMPLATE: The default page template.

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
        {{ header_content }}
    </head>
    <body>
        {{ js_templates }}
        <div class='discovery-area'></div>
        {{ body_content }}
    </body>
</html>
    """

    # Django templates
    page = models.TextField(default=DEFAULT_PAGE, verbose_name='Page')

    # not necessarily "all lower case attributes in this class"
    # TODO: check if theme editor is affected
    THEMABLE_ATTRIBS = ['page']

    DEFAULT_STRING_BEFORE = "do not edit after this line"
    DEFAULT_STRING_AFTER = "do not edit before this line"

    def __init__(self, *args, **kwargs):
        super(StoreTheme, self).__init__(*args, **kwargs)
        self.CUSTOM_FIELDS = {
            'opengraph_tags': {
                'type': 'template',
                'values': ['pinpoint/campaign_opengraph_tags.html']
            },
            'head_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_head.html']
            },
            'body_content': {
                'type': 'template',
                'values': ['pinpoint/campaign_body.html']
            },
            'campaign_config': {
                'type': 'template',
                'values': ['pinpoint/campaign_config.html']
            },
            'js_templates': {
                'type': 'template',
                'values': ['pinpoint/default_templates.html']
            }
        }

    def __unicode__(self):
        return u"Theme: %s" % self.name

    def get_styles(self, theme_str, block_name,
                   string_before=DEFAULT_STRING_BEFORE,
                   string_after=DEFAULT_STRING_AFTER,
                   return_filler=False):
        """Return a string with the contents surrounding a theme struct
        similar to this one:

        /* do not edit after this line (.youtube) */
        p { background: red; }
        /* do not edit before this line (.youtube) */

        In which case, "p { background: red; }" is returned
            if block_name == '.youtube'.
        """
        rej = re.compile(r'''# /* do not... (selector) */
                            \/\*\s+{0}\s+\({1}\)\s+\*\/
                            # styles (captured, non-greedy)
                            (.*?)
                            # provided that it is followed by /* do not... (same selector) */
                            (?=\/\*\s+{2}\s+\({3}\)\s+\*\/)
                            '''.format(re.escape(string_before),
                                       re.escape(block_name),
                                       re.escape(string_after),
                                       re.escape(block_name)),
                         re.M | re.I | re.S | re.X)
        found_styles = rej.findall(theme_str)
        if found_styles and found_styles[0].strip():
            return found_styles[0].strip()
        else:  # found_styles == None
            if return_filler:
                return '%s {\n    \n}\n' % block_name # blank style
            else:
                return ''


    def set_styles(self, style_map,
                   string_before=DEFAULT_STRING_BEFORE,
                   string_after=DEFAULT_STRING_AFTER):
        """Return a StoreTheme object with all styles updated according to
        style_map, which is a dict: {"block_selector": "rules"}.

        /* do not edit after this line (.youtube) */
        /* do not edit before this line (.youtube) */

        In which case, the theme will be updated with p { background: red; }
            if blockwise_style_map contains ".youtube": "p { background: red; }".
        """
        for field in self.THEMABLE_ATTRIBS:
            # field == 'shop_the_look', 'featured_product', ...
            for selector, styles in style_map.iteritems():
                #  selector = '.block'; styles == '.block { ... }'
                find_str = r'''# /* do not... (selector) */
                               \/\*\s+{0}\s+\({1}\)\s+\*\/
                               # styles (captured, non-greedy)
                               (.*?)
                               # provided that it is followed by /* do not... (same selector) */
                               (?=\/\*\s+{2}\s+\({3}\)\s+\*\/)
                               '''.format(re.escape(string_before),
                                          re.escape(selector),
                                          re.escape(string_after),
                                          re.escape(selector))
                sub_pattern = '/* %s (%s) */\n%s\n' % (
                    string_before, selector, styles)
                setattr(self, field,
                        re.sub(find_str, sub_pattern, getattr(self, field, ''),
                               0, re.M | re.I | re.S | re.X))


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
    theme = models.ForeignKey(StoreTheme,
        related_name='theme',
        blank=True,
        null=True,
        verbose_name='Campaign Theme')
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
            ir_campaign = IntentRankCampaign(
                name=self.name,
                slug=self.slug,
                description=self.description
            )
            ir_campaign.save()

            self.default_intentrank = ir_campaign
            self.intentrank.add(ir_campaign)

    def get_theme(self, theme_type='auto'):
        """Returns the best match for the given theme type.

        type: a string; either 'full' or 'mobile'
        """
        priorities = {'auto': [self.theme,
                               self.store.theme,
                               None]}

        themes = priorities.get(theme_type)
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
