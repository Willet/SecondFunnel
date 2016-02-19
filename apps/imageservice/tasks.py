import base64
from cloudinary.utils import cloudinary_url as generate_cloudinary_url
from django.conf import settings
import mimetypes
import os
from PIL import ImageFilter, Image
import re
from StringIO import StringIO
from threading import Semaphore
import urllib2

from apps.imageservice.models import SizeConf
from apps.imageservice.utils import create_image, create_image_path, delete_cloudinary_resource, \
                                    get_filetype, get_public_id, IMAGE_SIZES, upload_to_cloudinary, \
                                    within_color_range
from apps.utils.aws import upload_to_bucket


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
        if not SizeConf.objects.filter(name=name).exists():
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
        width, height = size.width, size.height
        resized = img.resize(width, height, Image.ANTIALIAS)
        resized = resized.filter(ImageFilter.UnsharpMask)  # Unsharpen image
        image_sizes.append(resized)

    return image_sizes


def download_image(source_url):
    """
    Downloads an image from source_url

    @param source_url
    @return: ExtendedImage object
    """
    # download here
    download = urllib2.urlopen(source_url, timeout=10)
    return create_image(download)


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


def upload_to_s3(path, folder, img, file_id):
    """
    Uploads an image to S3, avoids a disk write by keeping the image
    in memory.

    @param path: prefixed path name
    @param folder: The unique folder to store it in
    @param img: <ExtendedImage> object
    @param file_id: desired file name sans extension
    @return: url of s3 resouce
    """
    buff = StringIO()  # save into a string to avoid disk write
    img.save(buff)
    buff.seek(0) # rewind to start of file

    file_format = "jpg" if img.format is None else img.format.lower()
    filename = "{0}.{1}".format(file_id, file_format)

    bucket = os.path.join(settings.IMAGE_SERVICE_BUCKET, path, folder)

    if not upload_to_bucket(
            bucket_name=bucket,
            filename=filename, content=buff,
            content_type=mimetypes.MimeTypes().guess_type(filename)[0],
            public=True,
            do_gzip=True):
        raise IOError("ImageService could not upload size.")

    return os.path.join(bucket, filename)


def upload_gif_to_s3(folder, source):
    filename = source.name
    # source file is initially read when uploaded, must set seek to 0
    # otherwise read() returns an empty string
    # https://code.djangoproject.com/ticket/7812#no1
    source.file.seek(0)
    image_data = source.file.read()
    bucket = os.path.join(settings.IMAGE_SERVICE_BUCKET, folder)

    if not upload_to_bucket(
            bucket_name=bucket,
            filename=filename, content=image_data,
            content_type=mimetypes.MimeTypes().guess_type(filename)[0],
            public=True,
            do_gzip=True):
        raise IOError("ImageService could not upload size.")

    return os.path.join(bucket, filename)


def process_gif(source, path='', sizes=None, remove_background=False):
    """
    Processes a gif, uploads jpg version to cloudinary, uploads gif to s3.

    @param source: An UploadedFile containing the image.
    @param path: The path to save the object to
    @param sizes: List of sizes to create (unused)
    @return: object
    """
    data = process_image(source, path, sizes=sizes, remove_background=remove_background)
    s3_url = "http://" + upload_gif_to_s3(path, source)
    data.update({ 'gif_url': s3_url })

    return data



def process_image(source, path='', sizes=None, remove_background=False, forced_image_ratio=False):
    """
    Acquires a lock in order to process the image.

    @param source: Name of the image source
    @param path: The path to save the object to
    @param sizes: List of sizes to create (unused)
    @param remove_background: Either hex color str (ex: "#996633") or False
    @param forced_image_ratio: Either integer width/height ratio (ex: 1.5) or False
    @return: object
    """
    if not sizes:
        sizes = []

    with PROCESSING_SEM:
        data = process_image_now(source, path,
                                 sizes=sizes,
                                 remove_background=remove_background,
                                 forced_image_ratio=forced_image_ratio)

    return data


def process_image_now(source, path='', sizes=None, remove_background=False, forced_image_ratio=False):
    """
    Delegates to resize to create the necessary sizes.

    See all Cloudinary options:
    http://cloudinary.com/documentation/django_image_upload#all_upload_options

    @param source: Name of the image source
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
    kwargs = {}
    trimmed_object = None
    color = None if remove_background == 'uniform' else remove_background

    if (remove_background is not False) and ((remove_background == 'auto') or within_color_range(source, color, 4)):
        print "trimming"
        trimmed_object = upload_to_cloudinary(source, path=path, effect='trim')
        trimmed_ratio = (float(trimmed_object['height'])/trimmed_object['width'])
        print "trimmed_ratio:", trimmed_ratio
     
    if forced_image_ratio is not False:
        # force image ratio by padding image
        kwargs['crop'] = 'pad'

        if not trimmed_object:
            trimmed_object  = upload_to_cloudinary(source, path=path)
        desired_ratio = float(forced_image_ratio)
        actual_ratio = (float(trimmed_object['width']) / trimmed_object['height'])

        if actual_ratio > desired_ratio:
            # Too wide-y
            kwargs['width'] = trimmed_object['width']
            kwargs['height'] = int(float(trimmed_object['width']) / desired_ratio)
        else:
            # Too tall-ey
            kwargs['height'] = trimmed_object['height']
            kwargs['width'] = int(float(trimmed_object['height']) * desired_ratio)

        image_object = upload_to_cloudinary(trimmed_object['url'], path=path, **kwargs)
        delete_cloudinary_resource(trimmed_object['url']) # destroy the temporary
    elif trimmed_object:
        # force standard aspect ratios (3:4, 1:1, or 2:1) on trimmed images
        kwargs['crop'] = 'pad'

        aspect_ratios = {0.75: 'portrait', 1: 'square', 2: 'landscape'}
        keys = sorted(aspect_ratios.keys())
        msg = "padding {} dimension, bringing image ratio to {} ({})"

        for index, ratio in enumerate(keys):
            if trimmed_ratio < ratio:
                print msg.format('x', ratio, aspect_ratios[ratio])
                kwargs['width'] = int(trimmed_object['height'] * ratio)
                kwargs['height'] = trimmed_object['height']
                break
            # find the tipping point between this ratio and the next.
            # also, if this is the last ratio.
            elif index+1 == len(keys) or trimmed_ratio < float(ratio + keys[index+1]) / 2:
                print msg.format('y', ratio, aspect_ratios[ratio])
                kwargs['width'] = trimmed_object['width']
                kwargs['height'] = int(trimmed_object['width'] / ratio)
                break

        image_object = upload_to_cloudinary(trimmed_object['url'], path=path, **kwargs)
        delete_cloudinary_resource(trimmed_object['url']) # destroy the temporary
    else:
        print "Not resizing because of spider settings"
        print "To enable trimming and resizing, change \"remove_background\" and/or \"forced_image_ratio\""
        image_object = upload_to_cloudinary(source, path=path)

    # Grab the dominant color from cloudinary
    colors = image_object['colors']
    colors = sorted(colors, key=lambda c: c[1], reverse=True)
    dominant_color = colors[0][0]
    master_url = image_object['url']
    print master_url
    img_format = image_object['format']

    # cloudinary resizes images on their end
    data['sizes']['master'] = {
        'width': image_object['width'],
        'height': image_object['height'],
        'url': master_url,
    }

    data.update({
        'url': master_url,
        'format': img_format,
        'dominant_color': dominant_color
    })

    return data


def transfer_cloudinary_image_to_s3(cloudinary_url, store, size):
    """ Transfer one size of cloudinary image to S3.

    Acquires a lock in order to process the image.

    @param source: Name of the image source
    @param path: The path to save the object to
    @param sizes: List of sizes to create (unused)
    @return: object

    Returns (<ExtendedImage>, s3 url)
    """
    with PROCESSING_SEM:
        data = transfer_image_now(cloudinary_url, store, size)

    return data


def transfer_image_now(cloudinary_url, store, size):
    # cloudinary resizes images on their end
    # Ex: http://res.cloudinary.com/secondfunnel/image/upload/c_fit,q_75,w_700
    #            /v1441808046/sur%20la%20table/539a3d9b66907635.jpg
    # is saved as:
    #     http://images.secondfunnel.com/store/surlatable/tile/539a3d9b66907635.jpg
    cloudinary_public_id = get_public_id(cloudinary_url)
    filetype = get_filetype(cloudinary_url)
    path = create_image_path(store.id, 'sizes') # returns ex: "/surlatable/sizes/"
    # NOTE: if JS resizing changes, need to update this:
    cloudinary_url = generate_cloudinary_url(u"{}.{}".format(cloudinary_public_id, filetype),
                                             width=size.width, height=size.height,
                                             crop="fit", quality=75)[0]
    img = download_image(cloudinary_url)

    # Cloudinary ids include store name and sometimes other folders, grab just the end ID
    # Turns sur%20la%20table/539a3d9b66907635 into 539a3d9b66907635
    id_parts = [re.search(r"/([^/]+)$", cloudinary_public_id).group(1), size.width, size.height]
    id_format = "{0}_{1}x{2}" if size.width and size.height else \
                "{0}_w{1}" if size.width else "{0}_h{2}"
    s3_public_id = id_format.format(*id_parts)

    s3_url = u"http://" + upload_to_s3(path, size.name, img, s3_public_id)

    return (img, s3_url)
    
