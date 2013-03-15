"""Image Service helpers"""

import json
import urllib2

def queue_processing(store_slug, image_type, image_url, product_id=0):
    """Very basic way to queue images into ImageService"""

    api_base = "http://imageservice.elasticbeanstalk.com"
    api_storage_base = "http://images.secondfunnel.com"

    api_call = "{0}/images/{1}/product/{2}/{3}/queuebyurl?sourceUrl={4}".format(
        api_base, store_slug, product_id, image_type, image_url)

    res = json.load(urllib2.urlopen(api_call))
    master_image = "{0}/{1}/{2}/master.jpg".format(
        api_storage_base, res['imageFolder'], res['imageId'])

    return master_image
