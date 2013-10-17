from django.db import models

from django.contrib.contenttypes import generic


class StaticLog(models.Model):
    LOG_TYPES = (
        ('BU', 'Static Website Bucket'),
        ('CD', 'Static Campaign Desktop Page'),
        ('PE', 'Pending'),
    )

    object_id = models.PositiveIntegerField()
    parent = generic.GenericForeignKey('content_type', 'object_id')

    key = models.CharField(max_length=2, choices=LOG_TYPES)

    timestamp = models.DateTimeField(auto_now_add=True)
