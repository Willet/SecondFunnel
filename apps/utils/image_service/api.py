"""Image Service API implementation"""

import json
import urllib2

def queue_processing(image_url,
    store_slug="generic", image_type="generic",product_id=0):

    """Very basic way to queue images into ImageService"""

    api_base = "http://imageservice.elasticbeanstalk.com"
    api_storage_base = "http://images.secondfunnel.com"

    api_call = "{0}/images/{1}/product/{2}/{3}/queuebyurl?sourceUrl={4}".format(
        api_base, store_slug, product_id, image_type, image_url)

    try:
        res = json.load(urllib2.urlopen(api_call))

    except (urllib2.URLError, urllib2.HTTPError, ValueError):
        return None

    else:
        master_image = "{0}/{1}/{2}/master.jpg".format(
            api_storage_base, res['imageFolder'], res['imageId'])

        return master_image
