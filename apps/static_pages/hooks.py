"""
Model hooks that invoke appropriate celery tasks
"""

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
