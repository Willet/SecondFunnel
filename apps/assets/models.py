from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import striptags


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
        fields = [
            ('data-title', striptags(self.name),),
            ('data-description', striptags(self.description),),
            ('data-price', striptags(self.price),),
            ('data-url', striptags(self.original_url),),
            ('data-images', '|'.join(striptags(x) for x in self.images())),
        ]

        data = ' '.join("%s='%s'" % field for field in fields)

        tag = u'<span class="data" {data}></span>'.format(data=data)
        return tag


class ProductMedia(ImageBase):
    product = models.ForeignKey(Product, related_name="media")
