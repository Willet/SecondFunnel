"""
Model hooks that invoke appropriate celery tasks
"""
from django.db.models.signals import post_save

from apps.assets.models import Store
from apps.pinpoint.models import Campaign

from apps.static_pages.tasks import (generate_static_campaign,
    create_bucket_for_store)

def campaign_saved(sender, instance, created, **kwargs):
    """
    Uploads saved campaign to S3
    """

    generate_static_campaign.delay(instance.id)


def store_saved(sender, instance, created, **kwargs):
    """
    Creates a static website bucket for the saved store, if one doesn't already exist
    """
    create_bucket_for_store.delay(instance.id)

post_save.connect(store_saved, sender=Store)
post_save.connect(campaign_saved, sender=Campaign)
