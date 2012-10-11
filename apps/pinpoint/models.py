from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from apps.assets.models import MediaBase, BaseModel, BaseModelNamed, Store


class StoreThemeMedia(MediaBase):
    theme = models.ForeignKey("StoreTheme", related_name="media")


class StoreTheme(BaseModelNamed):
    store = models.ForeignKey(Store)
    css = models.TextField(blank=True, null=True)

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
    store = models.ForeignKey(Store)
    content_blocks = models.ManyToManyField(BlockContent,
        related_name="content_campaign")

    discovery_blocks = models.ManyToManyField(BlockContent,
        related_name="discovery_campaign")

    def __unicode__(self):
        return u"Campaign: %s" % self.name
