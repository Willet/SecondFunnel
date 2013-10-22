"""
Model hooks that invoke appropriate celery tasks
"""
from django.db.models.signals import post_save

from apps.assets.models import Store
from apps.pinpoint.models import Campaign

from apps.static_pages.tasks import (generate_static_campaign,
    generate_static_campaign_now, create_bucket_for_store,
    create_bucket_for_store_now)

def campaign_saved(sender, instance, created, **kwargs):
    """
    Uploads saved campaign to S3
    """
    try:
        generate_static_campaign.delay(instance.store.id, instance.id)
        return
    except:
        pass  # TODO: investigate [Errno 111] Connection refused

    try:
        generate_static_campaign_now(instance.store.id, instance.id)
        return
    except:
        pass  # TODO: investigate [Errno 111] Connection refused


def store_saved(sender, instance, created, **kwargs):
    """
    Creates a static website bucket for the saved store, if one
    doesn't already exist.

    instance is a store.
    """
    try:
        create_bucket_for_store.delay(instance.id)
        return
    except:
        pass  # TODO: investigate [Errno 111] Connection refused

    try:
        create_bucket_for_store_now(instance.id)
    except:
        pass


post_save.connect(store_saved, sender=Store)
post_save.connect(campaign_saved, sender=Campaign)
