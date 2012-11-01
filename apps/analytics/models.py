"""
Models representing calculated Analytics results.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class AnalyticsBase(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        abstract = True


class AnalyticsData(AnalyticsBase):
    date = models.DateTimeField()

    key = models.CharField(max_length=255)
    value = models.IntegerField()

    class Meta:
        verbose_name_plural = "Analytics Data"

    def __unicode__(self):
        return u"Analytics Data (key=%s, value=%s) for %s" % (
            self.key, self.value, self.parent)


class AnalyticsRecency(AnalyticsBase):
    last_fetched = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Analytics Recency"

    def __unicode__(self):
        return u"Analytics Recency for %s: %s" % (
            self.parent, self.last_fetched)
