from django.contrib.auth.models import User
from django.db import models


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

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
    remote = models.CharField("Remote URL",
        max_length=555, blank=True, null=True)

    hosted = models.FileField("Hosted File",
        upload_to="product_images", blank=True, null=True)

    media_type = models.CharField(max_length=3,
        choices=MEDIA_TYPES, default="css")

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


class Product(BaseModelNamed):
    original_url = models.CharField(max_length=500, blank=True, null=True)

    store = models.ForeignKey(Store, blank=True, null=True)

    price = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def media_count(self):
        return self.media.count()


class ProductMedia(MediaBase):
    product = models.ForeignKey(Product, related_name="media")
