"""
Models representing calculated Analytics results.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class AnalyticsRecency(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey('content_type', 'object_id')

    last_fetched = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Analytics Recency"

    def __unicode__(self):
        return u"Analytics Recency for %s: %s" % (
            self.parent, self.last_fetched)


class AnalyticsBase(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Category(AnalyticsBase):
    metrics = models.ManyToManyField("Metric", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __unicode__(self):
        return self.name

    def metrics_count(self):
        return self.metrics.all().count()

    def enabled_metrics(self):
        return self.metrics.filter(enabled=True)


class Metric(AnalyticsBase):
    data = models.ManyToManyField(
        "KVStore", related_name="data", blank=True, null=True)

    def __unicode__(self):
        return self.name

    def data_count(self):
        return self.data.all().count()


class KVStore(models.Model):
    content_type = models.ForeignKey(ContentType,
        related_name='analytics_data')

    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey(
        'content_type', 'object_id')

    target_type = models.ForeignKey(ContentType,
        blank=True, null=True, related_name='referred_in_analytics')
    target_id = models.PositiveIntegerField(blank=True, null=True)
    target = generic.GenericForeignKey(
        'target_type', 'target_id')

    key = models.CharField(max_length=255)
    value = models.FloatField()
    meta = models.CharField(max_length=255, blank=True, null=True)

    timestamp = models.DateTimeField()

    def __unicode__(self):
        return u"%s:%s (%s)" % (self.key, self.value, self.timestamp)
