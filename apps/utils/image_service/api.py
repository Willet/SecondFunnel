"""Image Service API implementation"""

import json
import urllib2

from django.conf import settings

def construct_api_url(image_url, store_slug, image_type, product_id):
    """
    >>> image_url = "http://example.com/image.jpg"
    >>> store_slug = "some-store"
    >>> image_type = "instagram"
    >>> product_id_1 = 0
    >>> product_id_2 = 123
    >>> construct_api_url(image_url, store_slug, image_type, product_id_1)
    'http://imageservice.elasticbeanstalk.com/images/some-store/instagram/queuebyurl?sourceUrl=http://example.com/image.jpg'
    >>> construct_api_url(image_url, store_slug, image_type, product_id_2)
    'http://imageservice.elasticbeanstalk.com/images/some-store/product/123/instagram/queuebyurl?sourceUrl=http://example.com/image.jpg'
    """

    if product_id == 0:
        return "{0}/images/{1}/{2}/queuebyurl?sourceUrl={3}".format(
            settings.IMAGE_SERVICE_API, store_slug, image_type, image_url)

    return "{0}/images/{1}/product/{2}/{3}/queuebyurl?sourceUrl={4}".format(
            settings.IMAGE_SERVICE_API, store_slug, product_id, image_type,
            image_url)

def queue_processing(image_url,
    store_slug="generic", image_type="generic", product_id=0):

    """Very basic way to queue images into ImageService"""

    api_url = construct_api_url(store_slug, product_id, image_type, image_url)

    try:
        res = json.load(urllib2.urlopen(api_url))

    except (urllib2.URLError, urllib2.HTTPError, ValueError):
        return None

    else:
        master_image = "{0}/{1}/{2}/master.jpg".format(
            settings.IMAGE_SERVICE_STORE, res['imageFolder'], res['imageId'])

        return master_image
