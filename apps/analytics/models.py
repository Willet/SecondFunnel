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
    metrics = models.ManyToManyField("Metric", through="CategoryHasMetric", blank=True, null=True)

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


class CategoryHasMetric(models.Model):
    category = models.ForeignKey(Category)
    metric = models.ForeignKey(Metric)

    order = models.PositiveIntegerField(default=0)
    display = models.BooleanField(default=True)

    is_meta = models.BooleanField(default=False)

    class Meta:
        ordering = ('-order',)


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


class SharedStorage(models.Model):
    """
    Amazon SQS has a size limit for its messages (64kb). At times we need to pass messages
    that are above that limit in size. In such cases, for convenience, we could use a "shared memory"
    approach - as opposed to breaking down and parallelizing message passing/processing, for example.
    """
    data = models.TextField()

    def __unicode__(self):
        return u"SharedStorage %d" % self.id
