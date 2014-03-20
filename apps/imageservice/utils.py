import os
import cStringIO
import urlparse

from django.conf import settings
from django.core.files.storage import default_storage

from apps.assets.models import Store
from apps.imageservice.models import ExtendedImage, SizeConf


# Constants
IMAGESERVICE_BUCKET = "images.secondfunnel.com"
IMAGESERVICE_USER_AGENT = "Mozilla/5.0 (compatible; SecondFunnelBot/1.0; +http://secondfunnel.com/bot.hml)"
IMAGESERVICE_USER_AGENT_NAME = "SecondFunnelBot"


IMAGE_SIZES = getattr(settings, 'IMAGE_SIZES', (
    ("pico", 16, 16),
    ("icon", 32, 32),
    ("thumb", 50, 50),
    ("small", 100, 100),
    ("compact", 160, 160),
    ("medium", 240, 240),
    ("large", 480, 480),
    ("grande", 600, 600),
    ("1024x1024", 1024, 1024),
    ("master", 2048, 2048)
))


def create_configuration(xpos, ypos, width, height):
    """
    Creates a new crop configuration.

    @param xpos: x-coordinate
    @param ypos: y-coordinate
    @param width: width of image
    @param height: height of image
    @return: Tuple
    """
    return (xpos, ypos, width, height)


def determine_format(url):
    """
    Determines format for file by grabbing extension.

    @param url: str
    @return: str
    """
    return url.split(".")[-1]


def create_image(source):
    """
    Creates an ExtendeImage object given the string representation of the
    image.

    @param source: str
    @return: ExtendedImage object
    """
    img = None

    try:
        buff = cStringIO.StringIO()
        buff.write(source)
        buff.seek(0)
        img = ExtendedImage.open(buff)
    except (IOError, OSError) as e:
        raise e

    return img


def create_image_path(store_id, *args):
    """
    Determine endpoint path for a url.
    """
    store = Store.objects.get(id=store_id)
    name = store.name.lower()

    if settings.ENVIRONMENT == 'dev':
        return os.path.join("store", name, *args)

    return urlparse.urljoin("store", name, *args)
