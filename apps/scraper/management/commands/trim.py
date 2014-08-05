from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import BaseCommand
from django.db.models import Q

from optparse import make_option
from apps.assets.models import ProductImage, Store
from apps.imageservice.tasks import process_image
from apps.imageservice.utils import delete_cloudinary_resource, get_public_id, create_image_path


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (make_option('--store-id', default=None, dest='store-id'),)

    def handle(self, *args, **kwargs):
        """
        If called with store-id (somehow) and url, scrapes that url for
            that store.
        Otherwise, scrapes all urls listed in all text files in the urls folder.
        """

        store_id = kwargs.pop('store-id', None)

        # allow either fields as identifiers
        if not store_id:
            raise ValueError("You need a store id (add '--store-id #' to the end)")

        try:
            Store.objects.get(Q(id=store_id) | Q(slug=store_id))
        except (Store.DoesNotExist, MultipleObjectsReturned) as err:
            raise ValueError("No such store")

        p = ProductImage.objects.filter(product__store_id=store_id)
        for image in p:
            delete_cloudinary_resource(get_public_id(image.url))
            data = process_image(image.original_url, create_image_path(5),
                                 remove_background='auto')
            image.url = data.get('url')
            image.file_type = data.get('format')
            image.dominant_color = data.get('dominant_colour')
            # save the image
            image.save()
        print "finished"
