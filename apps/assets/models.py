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


class Media(BaseModelNamed):
    remote = models.CharField("Remote URL",
        max_length=555, blank=True, null=True)

    hosted = models.FileField("Hosted File",
        upload_to="product_images", blank=True, null=True)

    def __unicode__(self):
        return u"Media Asset URL %s" % self.get_url()

    def get_url(self):
        if self.remote:
            return self.remote

        if self.hosted:
            return self.hosted.url

        return None


class Product(BaseModelNamed):
    price = models.CharField(max_length=255, blank=True, null=True)

    original_url = models.CharField(max_length=500, blank=True, null=True)
    images = models.ManyToManyField(Media, blank=True, null=True)

    def __unicode__(self):
        return self.name
