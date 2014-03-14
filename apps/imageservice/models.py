import numpy
import scipy
import scipy.misc
import scipy.cluster
from PIL import Image, ImageChops


MAX_COLOR_DISTANCE = 510


class ExtendedImage(object):
    """
    """

    def __init__(self, path=None, mode='RGBA', size=None, color="white"):
        if path is not None:
            self.path = path
            self._image = Image.open(path)
        else:
            self._image = Image.new(mode, size, color)

    def __getattr__(self, key):
        return getattr(self._image, key)

    def open(self, path, mode=None):
        """
        Opens the image pointed to by the path.

        @param self: ExtendedImage object
        @param path: String representing the full path to image
        @param mode: Mode to open object in
        @return: PIL.Image.Image
        """
        self.path = path

        if mode is not None:
            return self._image.open(path, mode)
        return self._image.open(path)

    def save(self, path=None, **options):
        """
        Saves the image.

        @param self: ExtendedImage object
        @param object: Dictionary of attributes to pass when saving object.
        @return: None
        """
        path = path if path is not None else self.path
        self._image.save(path, **options)

    def get_dominant_color(self, num_of_clusters=5):
        """
        Determines the dominant colour in an image and returns it as a hex string.
        Reference: http://stackoverflow.com/questions/3241929

        @param self: ExtendedImage object
        @param num_of_clusters: The number of clusters to generate.
        @return: String
        """
        # resize to reduce computation time
        tmp = self.copy().resize((150, 150))
        # Generate a histogram for the image colour points
        points = scipy.misc.fromimage(tmp)
        shape = points.shape
        points = points.reshape(scipy.product(shape[:2]), shape[2])

        # Using the kmeans algorithm, group the points into clusters
        clusters, _ = scipy.cluster.vq.kmeans(points, num_of_clusters)
        # Generate vectors
        vectors, distance = scipy.cluster.vq.vq(points, clusters)
        occurrences, _ = scipy.histogram(vectors, len(clusters)) # Get occurrences of each vector

        # Find most frequent colour
        peak = scipy.argmax(occurrences)
        peak = ''.join(chr(c) for c in clusters[peak]).encode('hex')

        return peak

    def get_edges(self, color):
        """
        Calculates the bounding box surrounding the non-white portion of the image; the
        box may contain portions of the specified color.
        Reference: http://stackoverflow.com/questions/9396312
        
        @param self: ExtendedImage object
        @param color: int representing pixel color
        @return: list
        """
        pixels = numpy.asarray(self)
        pixel = pixels[:, :, 0:3] # remove alpha channel

        colors = numpy.where(pixel - color)[0:2]
        box = map(min, colors)[::-1] + map(max, colors)[::-1]

        return box

    def trim(self, border=(255, 255, 255)):
        """
        Trims the border surrounding the focused image.  Default border
        is whitespace.

        @param self: ExtendedImage object
        @param border: Color to trim.
        @return: ExtendedImage object
        """
        bbox = self.get_edges(border)
        self._image = self.crop(bbox)

        return self

    def crop_color(self, color=(255, 255, 255)):
        """
        Crops the image based on the passed color.  Defaults to
        whitespace.

        @param self: ExtendedImage object
        @param color: The color to crop
        @return: ExtendedImage object
        """
        return self.trim(color)

    def make_transparent(self, color=(255, 255, 255), tolerance=0):
        # TODO: Make this functional
        """
        Makes all pixels within tolerance of the color transparent.  Defaults
        to a tolerance of 0, and whitespace.

        @param self: Image object
        @param color: Iterable of the RGB values
        @param tolerance: Float specifying tolerance in which to reject colors.
        @return: None
        """
        self._image = self.convert("RGBA")
        pixels = self.load()
        tolerance = MAX_COLOR_DISTANCE * tolerance

        for y in xrange(self.size[1]): # iterate over rows
            for x in xrange(self.size[0]): # iterate over cols
                data = pixels[x, y]
                diff = sum(abs(o - s) for o, s in zip(color, data))
                if diff <= tolerance:
                    pixels[x, y] = (255, 255, 255, 0)

        return self


if __name__ == "__main__":
    import sys

    img = ExtendedImage(sys.argv[1])
    img.make_transparent().show()
