from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
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


class UserProfile(models.Model):
    user = models.OneToOneField(User)


class MediaAsset(BaseModelNamed):
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
    images = models.ManyToManyField(MediaAsset, blank=True, null=True)

    def __unicode__(self):
        return self.name


class Store(BaseModelNamed):
    staff = models.ManyToManyField(User)

    def __unicode__(self):
        return self.name


class StoreTheme(BaseModelNamed):
    store = models.ForeignKey(Store)
    css = models.TextField(blank=True, null=True)
    assets = models.ManyToManyField(MediaAsset, blank=True, null=True)

    def __unicode__(self):
        return u"Theme for Store: %s" % self.store


class BlockType(BaseModelNamed):
    template_name = models.CharField(max_length=255)

    def __unicode__(self):
        return u"Block type: %s" % self.name


class BlockContent(BaseModel):
    block_type = models.ForeignKey(BlockType)
    priority = models.IntegerField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    data = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u"BlockContent of type %s for %s" % (
            self.content_type, self.block_type
        )


class Campaign(BaseModelNamed):
    content_blocks = models.ManyToManyField(BlockContent, related_name="content_campaign")
    discovery_blocks = models.ManyToManyField(BlockContent, related_name="discovery_campaign")

    def __unicode__(self):
        return u"Campaign: %s" % self.name
