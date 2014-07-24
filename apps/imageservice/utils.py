import hashlib
import re
import os
import math
import numpy
import random
import urlparse
import cStringIO
from collections import namedtuple

import cloudinary.api
import cloudinary.utils
import cloudinary.uploader
from django.conf import settings
from django.core.files.storage import default_storage

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


def get_public_id(url):
    """
    Returns the public ID of a cloudinary resource.

    @param url: The url of the uploaded resource
    @return: String
    """
    url = re.sub(r'(https?:)?' + settings.CLOUDINARY_BASE_URL, '', url)
    url = re.sub(r'/?image/upload/(.*?)/', '', url)
    public_id = ".".join(url.split('.')[:-1])

    return public_id


def upload_to_cloudinary(source, path='', effect=None):
    kwargs = {'folder': path,
              'colors': True,
              'format': 'jpg',
              'public_id': generate_public_id(source),
              'overwrite': True
              }

    if effect:
        kwargs.update({'effect': effect})
    image = cloudinary.uploader.upload(source, **kwargs)

    return image


def delete_cloudinary_resource(public_id):
    """
    Deletes the Cloudinary resource pointed to by the specified
    public id, or url.

    @param public_id: Url/id of resource, a string.
    @return: None
    """
    try:
        cloudinary.api.delete_resources(list(public_id))
    except cloudinary.api.NotFound:
        public_id = get_public_id(public_id)
        cloudinary.api.delete_resources(list(public_id))


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
    from apps.assets.models import Store

    store = Store.objects.get(id=store_id)
    name = store.name.lower()

    if settings.ENVIRONMENT == 'dev':
        return os.path.join("store", name, *args)

    return urlparse.urljoin("store", name, *args)


def hex_to_rgb(hex_color):
    """
    Turns the given hex code to rgb

    See http://codingsimplicity.com/2012/08/08/python-hex-code-to-rgb-value/ for details

    :param hex_color: the given hex to convert
    :return tuple(red, green, blue)
    """
    hex_color = hex_color.lstrip('#')

    hex_color = ''.join([x * 2 for x in hex_color]) if len(hex_color) == 3 else hex_color
    hlen = len(hex_color)
    color_length = hlen / 3
    return tuple(int(hex_color[i:i + color_length], 16) for i in range(0, hlen, color_length))


def euclidean_distance(p1, p2):
    """
    Returns the Euclidean distance between two points.

    @param p1: Point
    @param p2: Point
    @return: float
    """
    s = sum(list((p1.coords[i] - p2.coords[i]) ** 2 for i in range(p1.n)))
    return math.sqrt(s)


def within_color_range(url, color, threshold):
    """
    Uses cloudinary to determine if an image's background border is
    within a given color threshold. If color is None, will check if
    background is uniform.

    @param url: the location of the image file
    @param color: string containing the color
    @param threshold: int, amount average distance between colors must be less than
    @return boolean
    """
    nw_corner = cloudinary.uploader.upload(url, width=1, height=1,
                                           crop='crop', gravity='north_west',
                                           tags=['to_delete'], colors=True)["colors"]
    ne_corner = cloudinary.uploader.upload(url, width=1, height=1,
                                           crop='crop', gravity='north_east',
                                           tags=['to_delete'], colors=True)["colors"]
    se_corner = cloudinary.uploader.upload(url, width=1, height=1,
                                           crop='crop', gravity='south_east',
                                           tags=['to_delete'], colors=True)["colors"]
    sw_corner = cloudinary.uploader.upload(url, width=1, height=1,
                                           crop='crop', gravity='south_west',
                                           tags=['to_delete'], colors=True)["colors"]

    cloudinary.api.delete_resources_by_tag("to_delete")  # delete corners just uploaded

    points = [Point(hex_to_rgb(nw_corner[0][0]), 3, 0), Point(hex_to_rgb(ne_corner[0][0]), 3, 0),
              Point(hex_to_rgb(se_corner[0][0]), 3, 0), Point(hex_to_rgb(sw_corner[0][0]), 3, 0)]

    distance = 0

    if color:
        color = Point(hex_to_rgb(color), 3, 0)
        for point in points:
            distance += euclidean_distance(color, point)
        distance /= 4
    else:
        for corner1 in range(5):
            for corner2 in range(corner1 + 1, 4):
                distance += euclidean_distance(points[corner1], points[corner2])
        distance /= 6

    return True if distance <= threshold else False


def get_dominant_color(img, cluster_count=5, minimum_difference=1.0):
    """
    Finding the dominant colour in an image.  This is done by iterating over a random
    sample of clusters and finding the closest point, then taking the difference between that point
    and the old center point until the difference converges.  The more clusters, the better the result,
    but the slower it runs.

    Reference: http://charlesleifer.com/blog/using-python-and-k-means-to-find-the-dominant-colors-in-images/

    @param img: ExtendedImage object
    @param cluster_count: Integer
    @param minimum_difference: Float
    @return: String
    """
    points = []
    img = img.resize(200, 200)  # Resize for efficiency

    for count, color in img.getcolors(img.width * img.height):
        points.append(Point(color, 3, count))

    # Generate random clusters and find the centers
    clusters = kmeans(points, cluster_count, minimum_difference)

    rgb_values = list(map(int, c.center.coords) for c in clusters)
    rtoh = lambda rgb: '#%s' % ''.join(('%02x' % p for p in rgb))
    rgbs = map(rtoh, rgb_values)

    return rgbs[0]


def calculate_center(points, n):
    """
    Calculates the center between a set of points.

    @param points: List of Points
    @param n: Integer
    @return: Point
    """
    vals = [0.0 for i in range(n)]
    plen = 0

    # For each point, add its distance to the toal point length
    for p in points:
        plen += p.ct

        for i in range(n):
            vals[i] += (p.coords[i] * p.ct)

    # For each of the lengths between poitns divide by the total
    # distance to the center
    return Point([(v / plen) for v in vals], n, 1)


def kmeans(points, k, min_diff):
    """
    Kmeans algorithm for finding a histogram among a set of points.

    @param points: List of points
    @param k: The k-value
    @param min_diff: The minimum difference (tolerance)
    """
    clusters = [Cluster([p], p, p.n) for p in random.sample(points, k)]

    while True:  # iterate until convergence
        plists = [[] for i in range(k)]

        for p in points:

            smallest_distance = float('Inf')

            for i in range(k):
                distance = euclidean_distance(p, clusters[i].center)
                if distance < smallest_distance:
                    smallest_distance, idx = distance, i

            plists[idx].append(p)

        diff = 0
        for i in range(k):
            old = clusters[i]
            center = calculate_center(plists[i], old.n)
            new = Cluster(plists[i], center, old.n)
            clusters[i] = new
            diff = max(diff, euclidean_distance(old.center, new.center))

        if diff < min_diff:
            break

    return clusters


def generate_public_id(url, store=None, cloudinary_compatible=True):
    """Returns a string that is a product of a(n image) url and,
    optionally, the store from which this image was retrieved.

    if cloudinary_compatible is True, then the hash will be 16 characters long:
    http://cloudinary.com/documentation/django_image_upload#all_upload_options
    """
    if not url:
        raise ValueError("Cannot hash empty strings or other types")

    if store:
        url += store.slug + '/'

    url_hash = hashlib.md5(str(url)).hexdigest()
    if cloudinary_compatible:
        return url_hash[:16]
    return url_hash