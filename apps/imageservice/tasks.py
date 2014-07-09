import cStringIO
import mimetypes
from threading import Semaphore

import os
import cloudinary.utils
import cloudinary.uploader
from django.conf import settings
from PIL import ImageFilter, Image

from apps.imageservice.models import SizeConf
from apps.imageservice.utils import IMAGE_SIZES, within_color_range
from lib.aws_utils import upload_to_bucket



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
        resized = resized.filter(ImageFilter.UnsharpMask)  # Unsharpen image
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
    file_format = img.format or "jpg"
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
    output = cStringIO.StringIO()  # save into a string to avoid disk write
    img.save(output)

    file_format = "jpg" if img.format is None else img.format
    filename = "{0}.{1}".format(size.name, file_format)
    bucket = os.path.join(settings.IMAGE_SERVICE_BUCKET, path, folder)

    if not upload_to_bucket(
            bucket_name=bucket,
            filename=filename, content=output,
            content_type=mimetypes.MimeTypes().guess_type(filename)[0],
            public=True,
            do_gzip=True):
        raise IOError("ImageService could not upload size.")

    return os.path.join(bucket, filename)


def process_image(source, path='', sizes=None, remove_background=False):
    """
    Acquires a lock in order to process the image.

    @param source: The source file
    @param path: The path to save the object to
    @param sizes: List of sizes to create (unused)
    @return: object
    """
    if not sizes:
        sizes = []

    PROCESSING_SEM.acquire()
    try:
        data = process_image_now(source, path, remove_background=remove_background)
    except Exception as e:
        # Need to ensure semaphore is released
        PROCESSING_SEM.release()
        raise e

    PROCESSING_SEM.release()

    return data


def process_image_now(source, path='', sizes=None, remove_background=False):
    """
    Delegates to resize to create the necessary sizes.

    @param source: The source file
    @param path: The path to save the object to
    @param sizes: List of sizes to create
    @param remove_background: options to remove background
        - 'auto' - trim image regardless of colours
        - 'uniform' - trim image if background is uniform
        - '#colour' - trim image if background is colour (hex)
        - False - don't trim background
    @return: object
    """
    data = {'sizes': {}}

    color = None if remove_background == 'uniform' else remove_background
    if (remove_background is not False) and ((remove_background == 'auto') or within_color_range(source, color, 4)):
        print "background removed"
        image_object = cloudinary.uploader.upload(source, folder=path, colors=True,
                                                  format='jpg', effect='trim')  # trim background
    else:
        image_object = cloudinary.uploader.upload(source, folder=path, colors=True,
                                                  format='jpg')

    # Grab the dominant colour from cloudinary
    colors = image_object['colors']
    colors = sorted(colors, key=lambda c: c[1], reverse=True)
    dominant_color = colors[0][0]
    master_url = image_object['url']
    img_format = image_object['format']

    # cloudinary resizes images on their end
    data['sizes']['master'] = {
        'width': image_object['width'],
        'height': image_object['height'],
    }

    data.update({
        'url': master_url,
        'format': img_format,
        'dominant-color': dominant_color
    })

    return data
