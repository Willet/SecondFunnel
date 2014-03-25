import os
import math
import numpy
import random
import urlparse
import cStringIO
from collections import namedtuple

from django.conf import settings
from django.core.files.storage import default_storage

from apps.assets.models import Store
from apps.imageservice.models import ExtendedImage


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


Point = namedtuple('Point', ('coords', 'n', 'ct'))
Cluster = namedtuple('Cluster', ('points', 'center', 'n'))


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


def euclidean_distance(p1, p2):
    """
    Returns the Euclidean distance between two points.

    @param p1: Point
    @param p2: Point
    @return: float
    """
    s = sum(list((p1.coords[i] - p2.coords[i]) ** 2 for i in range(p1.n)))
    return math.sqrt(s)


def get_dominant_color(img, cluster_count, minimum_difference=1.0):
    """
    Finding the dominant colour in an image.  This is done by iterating over a random
    sample of clusters and finding the closest point, then taking the difference between that point
    and the old center point until the difference converges.

    Reference: http://charlesleifer.com/blog/using-python-and-k-means-to-find-the-dominant-colors-in-images/

    @param img: ExtendedImage object
    @param cluster_count: Integer
    @param minimum_difference: Float
    @return: String
    """
    points = []
    for count, color in img.getcolors(img.width * img.height):
        points.append(Point(color, 3, count))

    # Generate random clusters and find the centers
    clusters = [Cluster([p], p, p.n) for p in random.sample(points, cluster_count)]

    while True:
        # Recalcuate the centers of each cluster until they converge
        # by iteration through the set of points
        plists = list([] for i in range(cluster_count))

        for p in points:
            smallest_distance = float('Inf')

            for i in range(cluster_count):
                distance = euclidean_distance(p, clusters[i].center)
                if distance < smallest_distance:
                    smallest_distance, idx = distance, i
            plists[idx].append(p) # shortest path

        difference = 0
        for i in range(cluster_count):
            old_cluster = clusters[i]
            # Recaculate the new center for this cluster
            values = list(0.0 for i in range(old_cluster.n))
            point_length = 0
            for p in plists[i]:
                point_length += p.ct
                values = list(values[i] + (p.coords[i] * p.ct) for i in range(old_cluster.n))
            center = Point([(v / point_length) for v in values], old_cluster.n, minimum_difference)
            new_cluster = Cluster(plists[i], center, old_cluster.n)
            clusters[i] = new_cluster

            # Recalculate difference, if it converges, return
            difference = max(difference, euclidance_distance(old_cluster.center, new_cluster.center))

        if difference < minimum_difference:
            break

    rgb_values = [map(int, c.cneter.coords) for c in clusters]
    rgb_values = map(lambda rgb: '%s' % ''.join(('%02x' % p for p in rgb_values)), rgbs)

    return rgb_values
