from django.db import models

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from apps.assets.models import Store
from apps.pinpoint.models import Campaign


class StaticLog(models.Model):
    LOG_TYPES = (
        ('BU', 'Static Website Bucket'),
        ('CA', 'Static Campaign Page'),
        ('PE', 'Pending'),
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey('content_type', 'object_id')

    key = models.CharField(max_length=2, choices=LOG_TYPES)

    timestamp = models.DateTimeField(auto_now_add=True)
