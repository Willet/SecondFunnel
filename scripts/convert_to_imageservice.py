from apps.assets.models import GenericImage
from apps.utils.image_service.hooks import process_image

for im in GenericImage.objects.all():
    process_image(im)
