"""Image Service model hooks"""

from django.conf import settings

from apps.utils.image_service.api import queue_processing, queue_upload


def process_image(instance):
    instance.remote = queue_upload(instance.hosted.file)
    if instance.remote:
        instance.hosted = None
        instance.save()


def media_saved(sender, instance, created, **kwargs):
    """Saves GenericImage URLs with those hosted by the ImageService"""

    if created:
        process_image(instance)
