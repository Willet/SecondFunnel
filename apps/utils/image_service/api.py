"""Image Service API implementation"""

import json
import urllib2

from django.conf import settings

def construct_api_url(image_url, store_slug, image_type, product_id):
    """Returns ImageService API URL based on parameters passed in"""

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
