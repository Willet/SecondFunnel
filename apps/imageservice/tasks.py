import os
import re
import json
import hashlib
import tempfile
import cStringIO
import mimetypes

import cloudinary.utils
import cloudinary.uploader
from threading import Semaphore
from django.conf import settings
from PIL import ImageFilter, Image

from apps.pinpoint.utils import read_remote_file
from apps.imageservice.utils import create_image, IMAGE_SIZES
from apps.imageservice.models import SizeConf, ExtendedImage
from apps.static_pages.aws_utils import upload_to_bucket, s3_key_exists


# Use a semaphore as image processing is an CPU expensive operation
# and don't want to drive our service into the ground
MAX_CONNECTIONS = getattr(settings, 'MAX_CONNECTIONS', 3)
PROCESSING_SEM = Semaphore(value=MAX_CONNECTIONS)


def check_configurations():
    """
    Checks for default configurations and creates them if they do
    not exist.
    """
    for (name, width, height) in IMAGE_SIZES:
        if not SizeConf.filter(name=name).exists():
            SizeConf(name=name, width=width, height=height).save()


def resize_images(sizes, img):
    """
    Resizes the image and returns a list of the sizes that were successfully
    created.

    @param sizes: list of SizeConfs
    @param img: ExtendedImage object
    @return: list of ExtendedImage object
    """
    image_sizes = []

    for size in sizes:
        name, width, height = size.name, size.width, size.height
        resized = img.resize(width, height, Image.ANTIALIAS)
        resized = resized.filter(ImageFilter.UnsharpMask) # Unsharpen image
        image_sizes.append(resized)

    return image_sizes


def upload_to_local(path, folder, img, size):
    """
    Uploads an image locally.

    @param path: The path where to upload the file
    @param folder: The unique folder to store it in
    @param img: ExtendedImage object
    @param size: SizeConf object
    @return: None
    """
    file_format = "jpg" if img.format is None else img.format
    filename = "{0}.{1}".format(size.name, file_format)

    if not os.path.exists(path):
        os.makedirs(path)

    filename = os.path.join(settings.STATIC_URL[1:],
                            path, folder, filename)
    
    with open(filename, 'wb') as output:
        img.save(output)

    return filename


def upload_to_s3(path, folder, img, size):
    """
    Uploads an image to S3, avoids a disk write by keeping the image
    in memory.

    @param bucket: prefixed path name
    @param folder: The unique folder to store it in
    @param img: ExtendedImage object
    @param size: SizeConf object
    @return: None
    """
    output = cStringIO.StringIO() # save into a string to avoid disk write
    img.save(output)

    file_format = "jpg" if img.format is None else img.format
    filename = "{0}.{1}".format(size.name, file_format)
    bucket = os.path.join(IMAGE_SERVICE_BUCKET, path, folder)

    if not upload_to_bucket(bucket_name=bucket,
        filename=filename, content=output,
        content_type=mimetypes.MimeTypes().guess_type(filename)[0],
        public=True, do_gzip=True):
        raise IOError("ImageService could not upload size.")

    return os.path.join(bucket, filename)


def process_image(source, path, sizes=[]):
    """
    Acquires a lock in order to process the image.

    @param source: The source file
    @param path: The path to save the object to
    @param sizes: List of sizes to create
    @return: None
    """
    PROCESSING_SEM.acquire()
    try:
        data = process_image_now(source, path)
    except Exception as e:
        # Need to ensure semaphore is released
        PROCESSING_SEM.release()
        raise e
    PROCESSING_SEM.release()

    return data


def process_image_now(source, path, sizes=[]):
    """
    Delegates to resize to create the necessary sizes.

    @param source: The source file
    @param path: The path to save the object to
    @param sizes: List of sizes to create
    @return: None
    """
    # TODO: More sophisticated determination of file object
    if re.match(r'^https?:', source):
        img, _ = read_remote_file(source)
        img = create_image(img)
    else:
        img = create_image(source)

    master_url, dominant_colour = None, None
    data = {'sizes': []}

    if len(sizes) == 0:
        sizes = (SizeConf(width=width, height=height, name=name)  for \
                 (name, width, height) in IMAGE_SIZES)

    # Get the unique folder where we'll store the image
    folder = hashlib.sha224(img.tobytes()).hexdigest()
    upload = upload_to_local if settings.ENVIRONMENT == 'dev' else \
        upload_to_s3

    if getattr(settings, 'CLOUDINARY', None) is not None:
        image_object = cloudinary.uploader.upload_image(source,
            folder=os.path.join(path, folder), public_id="master")
        master_url = "{0}.{1}".format(image_object.public_id,
                                      image_object.format)

    else: # fall back to default ImageService is Cloudinary is not available
        for size in sorted(sizes, key=lambda size: size.width):
            name, width, height = size.name, size.width, size.height
            resized = img.resize(width, height, Image.ANTIALIAS)
            resized = resized.filter(ImageFilter.UnsharpMask)

            try: # ignore on failure
                master_url = upload(path, folder, resized, size)
                data.sizes.update(dict(size.name, {
                    'width': size.width,
                    'height': size.height
                }))
            except (OSError, IOError) as e: # upload failed, don't add to our json
                continue

    data.update({
        'url': master_url,
        'format': img.format,
        'dominant-colour': img.dominant_colour
    })

    return data
