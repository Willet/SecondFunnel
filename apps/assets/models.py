from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import striptags
from django.utils.html import escape


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True


class BaseModelNamed(BaseModel):
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    slug = models.SlugField(blank=True, null=True)

    class Meta:
        abstract = True


class Store(BaseModelNamed):
    staff = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name

    def staff_count(self):
        return self.staff.all().count()


class MediaBase(BaseModelNamed):
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
        if self.remote:
            return self.remote

        if self.hosted:
            return self.hosted.url

        return None


class ImageBase(BaseModelNamed):
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
        if self.remote:
            return self.remote

        if self.hosted:
            return self.hosted.url

        return None


class GenericMedia(MediaBase):
    pass


class GenericImage(ImageBase):
    pass


class Product(BaseModelNamed):
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
        return self.media.count()

    # Template Aliases
    def url(self):
        return self.original_url

    def images(self):
        return [x.get_url() for x in self.media.all()]

    def data(self):
        def strip_and_escape(text):
            modified_text = striptags(text)
            modified_text = escape(modified_text)
            return modified_text

        images = self.images()
        image  = images[0] if images else None

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
    product = models.ForeignKey(Product, related_name="media")


class YoutubeVideo(BaseModel):
    video_id = models.CharField(max_length=11)
    store = models.ForeignKey(Store, null=True, related_name="videos")
