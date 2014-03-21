import os
import sys
from itertools import chain

from apps.imageservice.tasks import process_image_now
from apps.assets.models import ProductImage, Image


def upload():
    """
    Simple script that goes through the image objects updating them to the
    relative paths and uploading them to Cloudinary for use with the new
    SecondFunnel front-facing application.
    """
    secondfunnel_path = "http://images.secondfunnel.com/"
    result_list = list(chain(Image.objects.all(), ProductImage.objects.all()))

    for img in result_list:
        source = img.url
        # Get the relative path to use with Cloudinary
        if secondfunnel_path not in source:
            print "Skipping Image: %s" % source
            continue
        path = source.replace(secondfunnel_path, "")
        path = os.path.join(*(path.split("/")[:-2]))

        # Process the image now
        try:
            data = process_image_now(source, path)

        except IOError:
            print "Failed to process Image: %s" % source
            continue

        print "Processed Image: %s" % source
        img.url = data.get('url')
        img.save()

    print "Successfully transfered to Cloudinary."
