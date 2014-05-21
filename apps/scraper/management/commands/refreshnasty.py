from django.core.management.base import BaseCommand
from apps.assets.models import ProductImage
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import delete_cloudinary_resource, get_public_id, create_image_path


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        """
        If called with store-id (somehow) and url, scrapes that url for
            that store.
        Otherwise, scrapes all urls listed in all text files in the urls folder.
        """

        p = ProductImage.objects.filter(product__store=5)
        for image in p:
            delete_cloudinary_resource(get_public_id(image.url))
            data = process_image(image.original_url, create_image_path(5),
                                 remove_background='#FFF')
            image.url = data.get('url')
            image.file_type = data.get('format')
            image.dominant_color = data.get('dominant_colour')
            # save the image
            image.save()
        print "finished"
