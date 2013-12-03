import httplib2
import json

from django.contrib.auth.models import User
from django.core import serializers
from django.db import models
from django.db.models import get_model
from django.template.defaultfilters import striptags
from django.utils.html import escape

from social_auth.db.django_models import UserSocialAuth

from apps.contentgraph.models import ContentGraphObject
from apps.pinpoint.utils import read_a_file, read_remote_file


class BaseModel(models.Model):
    """
    The base model to inherit from.

    @ivar created: The date this database object was created.
    @ivar last_modified: The date this database object was last modified.
    """
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        """This is needed to allow other models to inherit from this one."""
        abstract = True


class BaseModelNamed(BaseModel):
    """
    The base model to inherit from when a models needs a name.

    @ivar name: The name of this database object.
    @ivar description: The description of this database object.

    @ivar slug: The short label for this database object. Often used in URIs.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    slug = models.SlugField(blank=True, null=True)

    class Meta:
        abstract = True

    def json(self):
        """default method for all models to have a json representation."""
        return serializers.get_serializer("json")().serialize(iter([self]))

    @classmethod
    def from_json(cls, json_data):
        """create an object from data. this is a subclassable stub."""
        return cls(**json_data)


class Store(BaseModelNamed):
    """
    This defines a store in the databse.

    @ivar staff: The users who are allowed to access this store's admin pages.
    """
    staff = models.ManyToManyField(User, related_name='stores')
    social_auth = models.ManyToManyField(UserSocialAuth, blank=True, null=True)

    theme = models.ForeignKey('pinpoint.StoreTheme',
        related_name='store',
        blank=True,
        null=True,
        verbose_name='Default theme')

    public_base_url = models.URLField(
        help_text="e.g. explore.nativeshoes.com", blank=True, null=True)

    features = models.ManyToManyField('assets.StoreFeature', blank=True,
        null=True, related_name='stores')

    def __init__(self, *args, **kwargs):
        try:
            super(Store, self).__init__(*args, **kwargs)
        except:
            # when __init__ doesn't take all keyword arguments, ignore exception
            pass

        # allow temporary storage of arbitrary attributes
        for key in kwargs:
            if not hasattr(self, key):
                setattr(self, key, kwargs[key])


    def __unicode__(self):
        return self.name

    def staff_count(self):
        """
        Gets the number of staff for this store.

        @return: The number of staff members for this store.
        """
        return self.staff.all().count()

    def live_campaigns(self):
        results = []
        live_campaigns = self.campaign_set.filter(live=True)
        for campaign in live_campaigns:
            intentrank_objects = campaign.intentrank.all()
            if intentrank_objects:
                results.extend(intentrank_objects)
            else:
                results.append(campaign)

        return results

    def features_list(self):
        return [x.slug for x in self.features.all()]

    @classmethod
    def from_json(cls, json_data):
        from apps.pinpoint.models import StoreTheme
        # special case... the theme needs to become an instance beforehand
        # automatically defaults to DEFAULT_PAGE
        theme = json_data.get('theme', '')
        if isinstance(theme, basestring):
            if not theme:
                theme = StoreTheme.DEFAULT_PAGE

            # try and load a remote theme file. if it fails, pass.
            theme = read_remote_file(theme, theme)

            # try to load a local theme file.
            # if that fails, default to the theme as if it were theme content.
            theme = read_a_file(theme, theme)
            json_data['theme'] = StoreTheme(page=theme)

        return cls(**json_data)


class StoreFeature(BaseModelNamed):
    def __unicode__(self):
        return self.name


class ImageBase(BaseModelNamed):
    """
    The base model for generic image assets.

    @ivar remote: The url of a remote asset. Either this or hosted
        must not be null.
    @ivar hosted: The hosted asset as a file.
    """
    remote = models.CharField(
        "Remote URL",
        max_length=555,
        blank=True,
        null=True)

    hosted = models.ImageField(
        "Hosted File",
        upload_to="product_images",
        blank=True,
        null=True)

    class Meta:
        abstract = True

    def get_url(self):
        """
        Gets a url to the asset. Prefers remote assets over hosted assets.

        @return: None if no url exists, or url to the asset.
        """
        if self.remote:
            return self.remote

        if self.hosted:
            return self.hosted.url

        return None

    def __unicode__(self):
        return self.get_url()


class GenericImage(ImageBase):
    """
    A non-meta version of ImageBase. This allows object that function as ImageBase
    objects while still allowing other models to extend ImageBase.
    """
    pass

class Product(BaseModelNamed):
    """
    Defines a product in the database.

    @ivar original_url: The url of the product page.
    @ivar store: The store the product is for.
    @ivar price: A string representing the price of the product.
    @ivar sku: The store's product id number.
    @ivar last_scraped: The date the product was last scraped. Used by Scraper.
    @ivar rescrape: Whether this product should be rescraped. Used by Scraper.
    @ivar lifestyleImage: An optional image of the product being used.

    """
    original_url = models.CharField(max_length=500, blank=True, null=True)

    store = models.ForeignKey(Store, blank=True, null=True)

    price = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)

    last_scraped = models.DateTimeField(blank=True, null=True)
    rescrape = models.BooleanField(default=False)

    available = models.BooleanField(default=True)

    # default values for non-db attributes
    tags = {}
    images = []
    lifestyle_image = ''
    template = 'product'

    def __unicode__(self):
        return unicode(self.name) or u''

    def json(self):
        """Change its default set of attributes to those defined in data()."""
        return json.dumps(self.data(raw=True))

    # Template Aliases
    def url(self):
        """
        @return: The url of the product page.
        """
        return self.original_url

    def data(self, raw=False):
        """HTML string representation of some of the product's properties.
        If raw, then the return value remains a dict.

        @return: A string containing data attributes for this product
        """
        def strip_and_escape(text):
            """
            Removes tags and escapes text for use in html.

            @param text: The text to strip tags and escape.

            @return: A string without tags and with special characters escaped.
            """
            modified_text = striptags(text)
            modified_text = escape(modified_text)
            return modified_text

        images = self.images

        fields = {
            'data-title': strip_and_escape(self.name),
            'data-description': strip_and_escape(self.description),
            'data-price': strip_and_escape(self.price),
            'data-url': strip_and_escape(self.original_url),
            'data-image': strip_and_escape(images[0]),
            'data-images': '|'.join(strip_and_escape(x) for x in images),
            'data-product-id': self.id,
            'data-template': 'product',
        }

        fields['data-tags'] = {}

        try:
            fields['data-lifestyle-image'] = self.lifestyle_image  # getter
            fields['data-template'] = self.template  # getter
        except AttributeError:  # product has no lifestyle images.
            pass

        if raw:
            data = {}
            for field in fields:
                # strip 'data-'
                field_name = field[5:]
                if field_name == 'images':
                    data[field_name] = filter(None, fields[field].split('|'))
                else:
                    data[field_name] = fields[field]
                    # exception for strip_and_escape edge case
                    if data[field_name] == "None":
                        data[field_name] = ""
        else:
            data = ''
            for field in fields:
                data = data + " %s='%s'" % (field, fields[field])

        return data


class YoutubeVideo(BaseModel):
    """
    Youtube videos that relate to a store.

    @ivar video_id: The youtube id of the video.
    @ivar store: The store this video is for.
    """
    video_id = models.CharField(max_length=11)
    store = models.ForeignKey(Store, null=True, related_name="videos")
    categories = models.ManyToManyField(
        get_model('pinpoint', 'IntentRankCampaign'),
        blank=True,
        null=True,
        related_name='videos'
    )


class PinpointIrCampaignProducts(models.Model):
    campaign = models.ForeignKey(get_model('pinpoint', 'Campaign'),)
    product = models.ForeignKey(Product)
    class Meta:
        db_table = u'pinpoint_ir_campaign_products'
        managed = False

    def __init__(self, *args, **kwargs):
        super(PinpointIrCampaignProducts, self).__init__(*args, **kwargs)
        raise PendingDeprecationWarning('what is this?')
