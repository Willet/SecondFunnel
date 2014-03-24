import os
import sys
import hashlib
import httplib2
import urlparse
from itertools import chain

import cloudinary.utils
from django.conf import settings

from apps.imageservice.utils import create_image
from apps.pinpoint.utils import read_remote_file
from apps.assets.models import ProductImage, Image
from apps.imageservice.tasks import process_image_now


def upload():
    """
    Simple script that goes through the image objects updating them to the
    relative paths and uploading them to Cloudinary for use with the new
    SecondFunnel front-facing application.
    """
    secondfunnel_path = "http://images.secondfunnel.com/"
    result_list = list(chain(Image.objects.all(), ProductImage.objects.all()))
    base_url = "http:{0}".format(settings.CLOUDINARY_BASE_URL)

    for img in result_list:
        source = img.url
        # Get the relative path to use with Cloudinary
        if secondfunnel_path not in source:
            print "Skipping Image, Already Processed: %s" % source
            continue
        path = source.replace(secondfunnel_path, "")
        path = os.path.join(*(path.split("/")[:-2]))

        # Process the image now
        try:
            image, _ = read_remote_file(source)
            image = create_image(image) # create the image

            # Determine the folder and get the appropriate cloudinary url
            folder = hashlib.sha224(image.tobytes()).hexdigest()
            folder = os.path.join(path, folder)
            url, fragments = base_url, [
                "/image/upload/",
                folder,
                "/master.{0}".format(image.format.lower().replace("jpeg", "jpg"))
            ]

            for fragment in fragments:
                url += fragment

            # Check for existance of the file
            c = httplib2.Http()
            response = c.request(url, "HEAD")
            if response[0]['status'] < 400:
                print "Skipping Image, Already Exists: %s" % source
                img.url = url
            else:
                data = process_image_now(source, path)
                print "Processed Image: %s" % source
                img.url = data.get('url')

        except IOError:
            print "Failed to process Image: %s" % source
            continue

        img.save()

    print "Successfully transfered to Cloudinary."
