import os
import json
import hashlib
import cStringIO
import mimetypes

from threading import Semaphore
from django.conf import settings
from PIL import ImageFilter, Image

from apps.imageservice.utils import IMAGE_SIZES
from apps.imageservice.models import SizeConf, ExtendedImage
from apps.static_pages.aws_utils import upload_to_bucket, s3_key_exists


# Use a semaphore as image processing is an CPU expensive operation
# and don't want to drive our service into the ground
MAX_CONNECTIONS = getattr(settings, 'MAX_CONNECTIONS', 2)
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


def upload_to_local(path, img, size):
    """
    Uploads an image locally.

    @param path: The path where to upload the file
    @param img: ExtendedImage object
    @param size: SizeConf object
    @return: None
    """
    file_format = "jpg" if img.format is None else img.format
    filename = "{0}.{1}".format(size.name, file_format)

    if not os.path.exists(path):
        os.makedirs(path)

    filename = os.path.join(path, filename)
    
    with open(filename, 'wb') as output:
        img.save(output)

    return None


def upload_to_s3(bucket, img, size):
    """
    Uploads an image to S3, avoids a disk write by keeping the image
    in memory.

    @param bucket: S3 bucket name + folder
    @param img: ExtendedImage object
    @param size: SizeConf object
    @return: None
    """
    output = cStringIO.StringIO() # save into a string to avoid disk write
    img.save(output)

    file_format = "jpg" if img.format is None else img.format
    filename = "{0}.{1}".format(size.name, file_format)

    if not upload_to_bucket(bucket_name=bucket,
        filename=filename, content=output,
        content_type=mimetypes.MimeTypes().guess_type(filename)[0],
        public=True, do_gzip=True):
        raise IOError("ImageService could not upload size.")

    return None


def process_image(source, path, sizes=[]):
    """
    Acquires a lock in order to process the image.

    @param source: The source file
    @param path: The path to save the object to
    @param sizes: List of sizes to create
    @return: None
    """
    PROCESSING_SEM.acquire()
    data = process_image_now(source, path)
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
    image_sizes = {}
    img = None

    try:
        buff = cStringIO.StringIO()
        buff.write(source)
        buff.seek(0) # reset seek pointer
        img = ExtendedImage.open(buff)
    except (IOError, OSError) as e:
        raise e

    if len(sizes) == 0:
        # sizes = SizeConf.objects.all()
        sizes = (SizeConf(width=width, height=height, name=name)  for (name, width, height) \
                     in IMAGE_SIZES)

    # Get the unique folder where we'll store the image
    folder = hashlib.sha224(img.tobytes()).hexdigest()
    path = os.path.join(path, folder)

    for size in sizes:
        name, width, height = size.name, size.width, size.height
        resized = img.resize(width, height, Image.ANTIALIAS)
        resized = resized.filter(ImageFilter.UnsharpMask)

        try:
            if settings.ENVIRONMENT == 'dev':
                upload_to_local(path, resized, size)
            else:
                upload_to_s3(path, resized, size)
            image_sizes[size.name] = { 
                'width': size.width,
                'height': size.height
            }
        except (OSError, IOError): # upload failed, don't add to our json
            continue

    return image_sizes
