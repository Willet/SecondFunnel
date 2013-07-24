"""
Models representing calculated Analytics results.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class AnalyticsRecency(models.Model):
    """The AnalyticsRecency model is not known to do anything.

    @ivar content_type: 
    @ivar object_id: 
    @ivar parent: 
    @ivar last_fetched: When the analytics data was last fetched.
    """
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
    """
    @ivar name: Name of the analytic.
    @ivar slug: Valid url generated from name.
    @ivar enabled: Whether or not this analytic is enabled.
    """
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Category(AnalyticsBase):
    """
    Different types of analytic events, e.g. Sharing, Engagement, Awareness.  Inherits
    from the AnalyticBase.

    @ivar metrics: Different metric model that are recorded.
    @ivar order: The object in which this model is returned when satisfying queries.
    @ivar default: Whether or not this Category is the default category for analtyics.
    """
    metrics = models.ManyToManyField("Metric", through="CategoryHasMetric",
                                     blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ('-order',)

    def __unicode__(self):
        return self.name

    def metrics_count(self):
        return self.metrics.all().count()

    def enabled_metrics(self):
        return self.metrics.filter(enabled=True)


class Metric(AnalyticsBase):
    """Stores the number of data points available for category metric.
    
    @ivar data: Different types of interaction objects.
    """
    data = models.ManyToManyField(
        "KVStore", related_name="metric", blank=True, null=True)

    def __unicode__(self):
        return self.name

    def data_count(self):
        return self.data.all().count()


class CategoryHasMetric(models.Model):
    """Class for supporting Many-to-Many relationships between
    Category and Metric.

    @ivar category: The associated category model.
    @ivar metric: The associated metric model.
    @ivar order: The order in which this model is returned when satisfying queries.
    @ivar display: Whether or not this model is rendered on analytic template pages.
    @ivar is_meta
    """
    category = models.ForeignKey(Category)
    metric = models.ForeignKey(Metric)

    order = models.PositiveIntegerField(default=0)
    display = models.BooleanField(default=True)

    is_meta = models.BooleanField(default=False)

    class Meta:
        ordering = ('-order',)


class KVStore(models.Model):
    """KVStore(Key-Value Store) is a data-pairing created by tasks to
    persist metrics

    KVStore objects are deleted by the redo_analytics task.
    
    @ivar content_type: 
    @ivar object_id: Id of a Metric object. 
    @ivar parent: Foreign key to a Metric object.
    @ivar target_type: 
    @ivar target_id: Id of a Category object.
    @ivar target: Foreign key to a Category object.
    @ivar key: The name corresponding to what type of analytic's data this is.
    @ivar value: The data being recorded.
    @ivar meta: The name corresponding to what source this data is from.
    @ivar timestamp: When the pairing was created.
    """
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

    @ivar data: Our message.
    """
    data = models.TextField()

    def __unicode__(self):
        return u"SharedStorage %d" % self.id
