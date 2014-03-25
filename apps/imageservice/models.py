import math
import numpy
import random
from PIL import Image, ImageChops, ImageFilter

from django.db import models


MAX_COLOR_DISTANCE = 510
NUM_OF_CLUSTERS = 5


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
    def new(cls, mode, size):
        """
        Creates a new ExtendedImage object.

        @param cls: ExtendedImage
        @param mode: Mode to open object in
        @param size: Tuple of the (width, height) dimensions
        @return: ExtendedImage
        """
        img = cls()
        img._image = Image.new(mode, size)
        return img

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
        from app.imageserver.utils import get_dominant_color

        colour = get_dominant_color(self, NUM_OF_CLUSTERS)
        return colour

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
        coefficients = (red_coefficient, green_coefficient, blue_coefficent)
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
