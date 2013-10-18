from django.db import models

from apps.assets.models import BaseModelNamed, Store


class StoreTheme(BaseModelNamed):
    """
    The database model for a store theme.

    @ivar DEFAULT_PAGE_TEMPLATE: The default page template.

    @ivar store_id: a number corresponding to a "store" in contentgraph.
    @ivar page_id: a number corresponding to a "page" in contentgraph.
                   this is optional.
    @ivar page: The template for the entire page. Css is also usually put here.
    """

    DEFAULT_PAGE = """
<!DOCTYPE html>
<html>
    <head>
        {{ campaign_config }}
        {{ head_content }}
    </head>
    <body>
        {{ js_templates }}
        <div class='discovery-area'></div>
        {{ body_content }}
    </body>
</html>
    """

    # Django templates
    page = models.TextField(verbose_name='Page', default=DEFAULT_PAGE)

    store_id = models.PositiveSmallIntegerField(null=False, blank=False)
    page_id = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        # unique_together: stackoverflow.com/a/2201687/1558430
        unique_together = ('store_id', 'page_id',)

    # not necessarily "all lower case attributes in this class"
    THEMABLE_ATTRIBS = ['page']

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

    def json(self):
        return {'page': self.page}

    @classmethod
    def from_json(cls, json_data):
        return cls(**json_data)


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


class IntentRankCampaign(BaseModelNamed):
    def __unicode__(self):
        return u'{0}'.format(self.name)


class Campaign(BaseModelNamed):
    """
    Defines a pinpoint page.

    @ivar store: The store this page is for.
    @ivar discovery_blocks: The discovery blocks for this page.
    @ivar live: Whether or not the current page is live.
    """
    store = models.ForeignKey(Store)
    theme = models.ForeignKey(StoreTheme,
        related_name='theme',
        blank=True,
        null=True,
        verbose_name='Campaign Theme')

    live = models.BooleanField(default=True)
    supports_categories = models.BooleanField(default=False)

    content_block = None  # stub

    intentrank = models.ManyToManyField(IntentRankCampaign,
        related_name='campaigns', blank=True, null=True)

    def __init__(self, *args, **kwargs):
        try:
            super(Campaign, self).__init__(*args, **kwargs)
        except:
            # when __init__ doesn't take all keyword arguments, ignore exception
            pass

        # allow temporary storage of arbitrary attributes
        for key in kwargs:
            if not hasattr(self, key):
                setattr(self, key, kwargs[key])

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

            self.intentrank.add(ir_campaign)

    @property
    def default_intentrank(self):
        try:
            return self.intentrank.all()[0]
        except IndexError:
            # TODO: raise if appropriate
            return 0

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

    @classmethod
    def from_json(cls, json_data):
        try:
            # special case... the theme needs to become an instance beforehand
            # automatically defaults to DEFAULT_PAGE
            theme = json_data.get('theme', '')
            if isinstance(theme, basestring):
                json_data['theme'] = StoreTheme(page=theme)
        except:
            json_data['theme'] = StoreTheme()  # fallback to default theme

        return cls(**json_data)
