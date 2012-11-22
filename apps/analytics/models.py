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


class Section(models.Model):
    name = models.CharField(max_length=100)
    categories = models.ManyToManyField("Category", blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    metrics = models.ManyToManyField("Metric", blank=True, null=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __unicode__(self):
        return self.name

    def metrics_count(self):
        return self.metrics.all().count()


class Metric(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)

    data = models.ManyToManyField(
        "KVStore", related_name="data", blank=True, null=True)

    def __unicode__(self):
        return self.name

    def data_count(self):
        return self.data.all().count()


class KVStore(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey('content_type', 'object_id')

    key = models.CharField(max_length=255)
    value = models.FloatField()
    timestamp = models.DateTimeField()

    def __unicode__(self):
        return u"%s:%s (%s)" % (self.key, self.value, self.timestamp)
