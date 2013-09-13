import json
import random
from django.contrib.auth.models import User
from django.db import models
from django.db.models import get_model
from django.template.defaultfilters import striptags
from django.utils.html import escape
from django.db.models.signals import post_save

from social_auth.db.django_models import UserSocialAuth

from apps.utils.image_service.hooks import media_saved


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
        fields = {}
        for field in self._meta.get_all_field_names():
            if field[:1] != '_':
                try:
                    fields[field] = unicode(getattr(self, field, None))
                except UnicodeEncodeError:
                    fields[field] = str(getattr(self, field, None))
                except:
                    pass  # bail on this particular attribute
        return json.dumps(fields)


class Store(BaseModelNamed):
    """
    This defines a store in the databse.

    @ivar staff: The users who are allowed to access this store's admin pages.
    """
    staff = models.ManyToManyField(User)
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


class StoreFeature(BaseModelNamed):
    def __unicode__(self):
        return self.name


class MediaBase(BaseModelNamed):
    """
    The base model for generic media assets.

    @ivar MEDIA_TYPES: The types of allowed media.
    @ivar remote: The url of a remote asset. Either this or hosted
        must not be null.
    @ivar hosted: The hosted asset as a file.
    @ivar media_type: The media type of this asset.

    @warning: Investigate adding "not null" restrictions on
        remote and hosted fields
    """
    MEDIA_TYPES = (
        ('js', 'JavaScript'),
        ('css', 'CSS'),
        ('img', 'Image'),
    )
    remote = models.CharField(
        "Remote URL",
        max_length=555, blank=True, null=True)

    hosted = models.FileField(
        "Hosted File",
        upload_to="product_images",
        blank=True,
        null=True)

    media_type = models.CharField(
        max_length=3,
        choices=MEDIA_TYPES,
        default="css",
        blank=True,
        null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return u"Media Asset URL %s" % self.get_url()

    def get_url(self):
        """
        Gets a url of the asset. Prefers remote assets over hosted assets.

        @return: None if no url exists, or url of the asset.
        """
        if self.remote:
            return self.remote

        if self.hosted:
            return self.hosted.url

        return None


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


class GenericMedia(MediaBase):
    """
    A non-meta version of MediaBase. This allows object that function as MediaBase
    objects while still allowing other models to extend MediaBase.
    """
    pass


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

    @ivar media: Related name for ProductMedia objects.
    """
    original_url = models.CharField(max_length=500, blank=True, null=True)

    store = models.ForeignKey(Store, blank=True, null=True)

    price = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)

    last_scraped = models.DateTimeField(blank=True, null=True)
    rescrape = models.BooleanField(default=False)

    lifestyleImages = models.ManyToManyField(GenericImage, blank=True, null=True,
                                       related_name='associated_products')

    default_image = models.ForeignKey("ProductMedia", blank=True, null=True,
                                      related_name='primary_product')

    available = models.BooleanField(default=True)

    def __unicode__(self):
        return unicode(self.name) or u''

    def media_count(self):
        """
        @return: The number of media objects associated to this product.
        """
        return self.media.count()

    def json(self):
        """Change its default set of attributes to those defined in data()."""
        return json.dumps(self.data(raw=True))

    # Template Aliases
    def url(self):
        """
        @return: The url of the product page.
        """
        return self.original_url

    def image(self):
        if self.default_image:
            return self.default_image.get_url()

        images = self.images()

        return images[0] if images else None

    def images(self, include_external=False):
        """if include_external, then all external media (e.g. instagram photos)
        will be included in the list.
        
        @return: A list of product image urls associated wih this product.
        """
        product_images = [x.get_url() for x in self.media.all()]
        if include_external:
            for external_content in self.external_content.all():
                if external_content.image_url:
                    product_images.append(external_content.image_url)

        # Default image should be first
        if self.default_image:
            first_image = self.default_image.get_url()
            if first_image in product_images:
                product_images.remove(first_image)
            product_images.insert(0, first_image)

        return product_images

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

        images = self.images()
        image = self.image()

        fields = {
            'data-title': strip_and_escape(self.name),
            'data-description': strip_and_escape(self.description),
            'data-price': strip_and_escape(self.price),
            'data-url': strip_and_escape(self.original_url),
            'data-image': strip_and_escape(image),
            'data-images': '|'.join(strip_and_escape(x) for x in images),
            'data-product-id': self.id,
            'data-template': 'product',
        }

        try:
            fields['data-tags'] = self.tags.tags

        # ProductTags.DoesNotExist
        except:
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

    def _get_preferred_template(self):
        """Does some check to find out if combo boxes are preferred.

        Clients may completely ignore this suggestion.
        """
        if self.lifestyleImages.all():
            return 'combobox'
        return 'product'

    # getter used by templating
    template = property(_get_preferred_template)

    def _get_random_lifestyle_image(self):
        """Returns a random lifestyle image url."""
        if self.lifestyleImages.all():
            random_idx = random.randint(0, self.lifestyleImages.count()-1)
            random_img = self.lifestyleImages.all()[random_idx]
            return unicode(random_img)
        raise AttributeError('No lifestyle image.')

    # getter used by templating
    lifestyle_image = property(_get_random_lifestyle_image)


class ProductMedia(ImageBase):
    """
    Images that relate to a product.

    @ivar product: The product this image is for.
    """
    product = models.ForeignKey(Product, related_name="media")


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


class ExternalContent(BaseModel):
    # "yes, 555 is arbitrary" - other developers
    original_id = models.CharField(max_length=555, blank=True, null=True)
    original_url = models.CharField(max_length=555, blank=True, null=True)
    content_type = models.ForeignKey("ExternalContentType")
    tagged_products = models.ManyToManyField(Product, blank=True, null=True,
                                             related_name='external_content')

    store = models.ForeignKey(Store, blank=True, null=True,
                                            related_name='external_content')

    categories = models.ManyToManyField(
        get_model('pinpoint', 'IntentRankCampaign'),
        blank=True,
        null=True,
        related_name='external_content'
    )

    text_content = models.TextField(blank=True, null=True)
    image_url = models.CharField(max_length=555, blank=True, null=True)

    likes = models.IntegerField(default=0, blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    user_image = models.CharField(max_length=555, blank=True, null=True)

    approved = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('original_id', 'content_type', 'store')

    def __unicode__(self):
        return u''

    def to_json(self):
        """A bit like data(), but not returning an html data string"""

        return {
            'original-id': self.original_id,
            'original-url': self.original_url,
            'url': self.original_url,
            'content-type': self.content_type.name,
            'image': self.image_url,
            'username': self.username,
            'user-image': self.user_image,
            'likes': self.likes,
            'caption': self.text_content
        }


# If we need different behaviour per model, just use a proxy model.
class ExternalContentType(BaseModelNamed):
    """i.e. "Instagram"."""
    enabled = models.BooleanField(default=True)
    classname = models.CharField(max_length=128, default='')

    def __unicode__(self):
        return unicode(self.name) or u''

class PinpointIrCampaignProducts(models.Model):
    campaign = models.ForeignKey(get_model('pinpoint', 'Campaign'),)
    product = models.ForeignKey(Product)
    class Meta:
        db_table = u'pinpoint_ir_campaign_products'
        managed = False


# signals
post_save.connect(media_saved, sender=GenericImage)
