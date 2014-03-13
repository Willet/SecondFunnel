from apps.assets.models import Image
from apps.utils.image_service.hooks import process_image

for im in Image.objects.all():
    process_image(im)
