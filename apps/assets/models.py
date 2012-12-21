from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import striptags
from django.utils.html import escape


class BaseModel(models.Model):
    """
    The base model to inherit from.

    @ivar created: The date this database object was created.
    @ivar last_modified: The date this database obeject was last modified.
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
    @ivar description: The description of this databse object.

    @ivar slug: The short label for this database object.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    slug = models.SlugField(blank=True, null=True)

    class Meta:
        """This is needed to allow other models to inherit from this one."""
        abstract = True


class Store(BaseModelNamed):
    """
    This defines a store in the databse.

    @ivar staff: The users who are allowed to access this store's admin pages.

    @ivar videos: Related name for YoutubeVideo objects.
    """
    staff = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name

    def staff_count(self):
        """
        Gets the number of staff for this store.

        @return: The number of staff for this store.
        """
        return self.staff.all().count()


class MediaBase(BaseModelNamed):
    """
    The base model for generic media assets.

    @ivar MEDIA_TYPES: The types of allowed media.
    @ivar remote: The url of a remote asset. Either this or hosted
        must not be null.
    @ivar hosted: The hosted asset as a file.
    @ivar media_type: The media type of this asset.
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
        """This is needed to allow other models to inherit from this one."""
        abstract = True

    def __unicode__(self):
        return u"Media Asset URL %s" % self.get_url()

    def get_url(self):
        """
        Gets a url to the asset. Prefers remote assets over hosted assets.

        @return: A url to the asset.
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
        """This is needed to allow other models to inherit from this one."""
        abstract = True

    def get_url(self):
        """
        Gets a url to the asset. Prefers remote assets over hosted assets.

        @return: A url to the asset.
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
    @ivar last_scraped: The date the product was last scraped.
    @ivar rescrape: Whether this product should be rescraped.
    @ivar lifestyleImage: An optional image of the product being used.

    @ivar media: Related name for ProductMedia objects.
    """
    original_url = models.CharField(max_length=500, blank=True, null=True)

    store = models.ForeignKey(Store, blank=True, null=True)

    price = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=255, blank=True, null=True)

    last_scraped = models.DateTimeField(blank=True, null=True)
    rescrape = models.BooleanField(default=False)

    lifestyleImage = models.ForeignKey(GenericImage, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def media_count(self):
        """
        Gets the number of media objects that refer to this product.

        @return: The number of media objects that refer to this product.
        """
        return self.media.count()

    # Template Aliases
    def url(self):
        """
        Gets the url of the product page.

        @return: The url of the product page.
        """
        return self.original_url

    def images(self):
        """
        Gets the urls of all images that refer to this product.

        @return: A list of product image urls.
        """
        return [x.get_url() for x in self.media.all()]

    def data(self):
        """
        Creates data attributes for use in html.

        @return: A string containing data attribues for this product.
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
        image = images[0] if images else None

        fields = [
            ('data-title', strip_and_escape(self.name)),
            ('data-description', strip_and_escape(self.description)),
            ('data-price', strip_and_escape(self.price)),
            ('data-url', strip_and_escape(self.original_url)),
            ('data-image', strip_and_escape(image)),
            ('data-images', '|'.join(strip_and_escape(x) for x in images)),
            ('data-product-id', self.id)
        ]

        data = ' '.join("%s='%s'" % field for field in fields)

        return data


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
