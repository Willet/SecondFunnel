"""Image Service model hooks"""

from apps.utils.image_service.api import queue_processing


def media_saved(sender, instance, created, **kwargs):
    """Saves GenericImage URLs with those hosted by the ImageService"""

    if created:
        image_url = instance.remote or instance.hosted

        instance.remote = queue_processing(image_url)
        if instance.remote:
            instance.hosted = None
            instance.save()
