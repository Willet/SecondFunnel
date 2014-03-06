"""Image Service model hooks"""

from django.conf import settings

from apps.utils.image_service.api import queue_processing


def process_image(instance):
    if instance.hosted and not instance.hosted.url.startswith("http"):
        image_url = "{0}{1}".format(settings.MEDIA_URL, instance.hosted)

    else:
        image_url = instance.remote or instance.hosted

    # both remote and hosted are missing
    if not image_url:
        return

    instance.remote = queue_processing(image_url)
    if instance.remote:
        instance.hosted = None
        instance.save()


def media_saved(sender, instance, created, **kwargs):
    """Saves GenericImage URLs with those hosted by the ImageService"""

    if created:
        process_image(instance)
