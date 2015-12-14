import collections
import json
import math

from django.db import models
import numpy
from PIL import Image

from .utils import delete_resource as delete_remote_resource
from .utils import get_dominant_color


MAX_COLOR_DISTANCE = 510


class SizeConf(models.Model):
    """
    A size configuration is a tool for resizing (create new resized
    images).
    """
    name = models.CharField(max_length=240)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()

    @property
    def size(self):
        """
        @return: Tuple
        """
        return (self.width, self.height)


class ImageSizes(collections.MutableMapping):
    """
    Holds various size representations of an image and methods
    A dict-like object with methods find & delete_resources

    Each size representation is a <dict> { 'width': ..., 'height': ..., 'url': ... }
    It is necessary to have one of width or height, but not both

    Will automatically delete remote resources on removal / over-writing
    """
    def __init__(self, internal_json=None):
        """
        internal_json should be provided by repr call on ImageSizes object.
        """
        if isinstance(internal_json, basestring) and internal_json:
            self._sizes = json.loads(internal_json)
        else:
            self._sizes = {}

    def __unicode__(self):
        return json.dumps(self._sizes, indent=2)

    def __repr__(self):
        return json.dumps(self._sizes)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               (sorted(self._sizes.items()) == sorted(other._sizes.items()))

    def __contains__(self, name):
        return (name in self._sizes)

    def __iter__(self):
        return iter(self._sizes)

    def __len__(self):
        return len(self._sizes)

    def __getitem__(self, key):
        return self._sizes[key]

    def __setitem__(self, key, value):
        self._add(key, value)

    def __delitem__(self, key):
        self._remove(key)

    def find(self, size):
        """
        Finds image size with matching width or height, width prioritized over height

        @param size: <dict> has keys width and/or height

        returns: (name <str>, size <dict>) or (None, None)
        """
        if not isinstance(size, dict):
            raise ValueError(u'Expected a dict, got {}'.format(type(size)))

        if size.get('width', None):
            return next(((name, obj) for name, obj in self._sizes.items()
                         if obj.get('width', None) == size.get('width')), (None, None))
        elif size.get('height', None):
            return next(((name, obj) for name, obj in self._sizes.items()
                         if obj.get('height', None) == size.get('height')), (None, None))
        else:
            return (None, None)

    def delete_resources(self):
        """
        Deletes all resources!
        """
        for name in self._sizes:
            self._remove(name, delete_resource=True)

    def _add(self, name, size, delete_existing_resource=True):
        """
        Adds image size with key name

        If an existing image size exists with the same name, it deletes that first

        @param name: string key
        @param size: <dict> must have a width and/or height key, optional url key (or anything else)
        """
        if not ('width' in size or 'height' in size):
            raise ValueError("size must have a width or height")

        if (name in self._sizes) and size.get('url', None) and \
            (self._sizes[name].get('url', None) != size.get('url')):
            # Replacing a size, so delete existing size & resource
            self._remove(name, delete_resource=delete_existing_resource)
        self._sizes[name] = size

    def _remove(self, name, delete_resource=True):
        """
        Deletes image size with name. If image size has url and delete_resource is True,
        the remote resource at url is deleted.

        @param name: key for size to delete
        @param delete_resource (optional): over-ride delete remote resource

        returns: True if match found & deleted, False if no match found
        """
        if name in self._sizes:
            obj = self._sizes[name]
            del self._sizes[name]
            if delete_resource and ('url' in obj):
                delete_remote_resource(obj['url'])
            return True
        else:
            return False


class COLOR(object):
    """
    Some colours.
    """
    red = (255, 0, 0)
    blue = (0, 0, 255)
    green = (0, 255, 0)
    black = (0, 0, 0)
    white = (255, 255, 255)


class ExtendedImage(object):
    """
    An ExtendedImage is an object extending PIL.Image to provide additional functionality
    while still maintaining the same use that PIL.Image provides.

    @attr path: The opened file path (if exists)
    """

    def __getattr__(self, key):
        """Delegate to PIL.Image"""
        result = getattr(self._image, key)

        if type(result) == Image:
            img = self.copy()
            img._image = result
            return img

        return result

    @classmethod
    def new(cls, mode, size, color):
        """
        Creates a new ExtendedImage object.

        @param cls: ExtendedImage
        @param mode: Mode to open object in
        @param size: Tuple of the (width, height) dimensions
        @param colour: Background colour to fill the image
        @return: ExtendedImage
        """
        img = cls()
        img._image = Image.new(mode, size, color)
        return img

    @classmethod
    def open(cls, path, mode=None):
        """
        Opens the image pointed to by the path and returns an opened
        ExtendedImage object.

        @param cls: ExtendedImage
        @param path: String representing the full path to image
        @param mode: Mode to open object in
        @return: ExtendedImage
        """
        img = cls()
        args = (path,) if mode is None else (path, mode)
        img.path = path
        img._image = Image.open(*args)

        return img

    @property
    def width(self):
        """
        Returns the width.
        """
        return self.size[0]

    @property
    def height(self):
        """
        Returns the height.
        """
        return self.size[1]

    @property
    def crop_conf(self):
        """
        Returns the default crop configuration for this image.

        @param self: The ExtendedImage instance
        @return: Tuple
        """
        return (0, 0, self.size[0], self.size[1])

    @property
    def dominant_color(self):
        """
        Determines the dominant colour in an image and returns it as a hex string.

        @param self: ExtendedImage instance
        @return: String
        """
        # resize to reduce computation time
        tmp = self.copy().resize(150, 150)
        # Generate a histogram for the image colour points
        # Begin by gathering into an array of points

        color = get_dominant_color(tmp)
        return color

    def copy(self):
        """
        Copies the ExtendedImage object and returns the copy.

        @param self: The ExtendedImage instance
        @return: ExtendedImage
        """
        img = ExtendedImage()
        img.path = getattr(self, 'path', None)
        img._image = self._image.copy()

        return img

    def save(self, path=None, mode=None, *args):
        """
        Saves the image.

        @param self: ExtendedImage instance
        @param object: Dictionary of attributes to pass when saving object.
        @return: None
        """
        path = path if path is not None else self.path
        mode = mode if mode is not None else self.format
        self._image.save(path, mode, *args)

    def luminosity(self, x, y, red_coefficient=0.2126, green_coefficient=0.7152, blue_coefficient=0.0722):
        """
        Computes the luminisoity in an image at the specified pixel.
        Takes the RGB pixel and determines the gray level intensity coefficient.

        @param self: ExtendedImage instance
        @param x: x-coordinate of the pixel
        @param y: y-coordinate of the pixel
        @param red_coefficient: Multiplier of the red value of the pixel.
        @param green_coefficient: Multiplier of the green value of the pixel.
        @param blue_coefficient: Multiplier of the blue value of the pixel.
        """
        coefficients = (red_coefficient, green_coefficient, blue_coefficient)
        rgb = self.getpixel((x, y))
        luminosity = sum(c * coeff for c, coeff in zip(rgb, coefficients))

        return luminosity

    def get_edges(self, color):
        """
        Calculates the bounding box surrounding the non-white portion of the image; the
        box may contain portions of the specified colour.
        Reference: http://stackoverflow.com/questions/9396312

        @param self: ExtendedImage instance
        @param colour: int representing pixel colour
        @return: list
        """
        pixels = numpy.asarray(self)
        pixel = pixels[:, :, 0:3] # remove alpha channel

        colors = numpy.where(pixel - color)[0:2]
        box = map(min, colors)[::-1] + map(max, colors)[::-1]

        return box

    def crop(self, border=COLOR.white, conf=None):
        """
        Crops the image based on the passed colour.  Defaults to
        whitespace.

        @param self: ExtendedImage instance
        @param border: The colour to crop
        @param conf: A tuple specifying the (x, y, width, height)
        @return: ExtendedImage object
        """
        img = self.copy()
        conf = conf if conf is not None else img.crop_conf
        img._image = img._image.crop(conf)

        # Get the bounding box
        bbox = img.get_edges(border)
        img._image = img._image.crop(bbox)

        return img

    def resize(self, targetWidth, targetHeight, *args):
        """
        Resizes and returns an ExtendedImage object.  If image is larger than
        our target, resizes based on the ratio, otherwise does not upscale the
        image.

        @param self: ExtendedImage instance
        @param targetWidth: The width to resize to.
        @param targetHeight: The height to resize to.
        @return: ExtendedImage
        """
        img = self.copy()
        width, height = None, None
        sourceWidth, sourceHeight = img.size

        if img.width <= targetWidth and img.height <= targetHeight:
            return img

        if img.width >= img.height: # image wider than it is tall
            width = targetWidth
            height = int(math.ceil((sourceHeight / float(sourceWidth)) * targetWidth))
        else:
            height = targetHeight
            width = int(math.ceil((sourceWidth / float(sourceHeight)) * targetHeight))

        img._image = img._image.resize((width, height), *args)

        return img

    def make_transparent(self, color=COLOR.white, tolerance=0.9):
        """
        Makes all pixels within tolerance of the colour transparent.  Defaults
        to a tolerance of 0, and whitespace.

        @param self: ExtendedImage instance
        @param colour: Iterable of the RGB values
        @param tolerance: Float specifying tolerance in which to reject colours.
        @return: None
        """
        self.convert('RGBA')
        pixels = self.load()
        tolerance = MAX_COLOR_DISTANCE * tolerance

        for y in xrange(self.size[1]): # iterate over rows
            for x in xrange(self.size[0]): # iterate over cols
                data = pixels[x, y]
                diff = sum(abs(o - s) for o, s in zip(color, data))
                if diff <= tolerance:
                    data = list(data)
                    data[3] = 0
                    pixels[x, y] = tuple(data)

        return self
