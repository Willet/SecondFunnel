import re

from django.utils import unittest
from django.conf import settings

from apps.utils.image_service.api import queue_processing, construct_api_url

class ImageServiceAPITests(unittest.TestCase):
    def setUp(self):
        pass

    def test_queue_processing_success(self):
        """
        ImageService API: success case
        """
        result_url = queue_processing(
            "http://farm9.staticflickr.com/8379/8456408563_643b2d30e0.jpg")

        self.assertNotEqual(result_url, None)

        re_test = re.compile("{0}/store/generic/generic/\w+/master\.jpg".format(
            settings.IMAGE_SERVICE_STORE))

        self.assertNotEqual(re_test.match(result_url), None)

    def test_queue_processing_error(self):
        """
        ImageService API: error case
        """
        result_url = queue_processing("blah")
        self.assertEqual(result_url, None)

    def test_construct_api(self):
        """
        Construct API url
        """

        image_url = "http://example.com/image.jpg"
        store_slug = "some-store"
        image_type = "instagram"
        product_id_1 = 0
        product_id_2 = 123

        # without product id
        result_url = construct_api_url(
            image_url, store_slug, image_type, product_id_1)

        self.assertEqual(result_url,
            "http://imageservice.elasticbeanstalk.com/images/some-store/instagram/queuebyurl?sourceUrl=http://example.com/image.jpg"
        )

        # with product id
        result_url = construct_api_url(
            image_url, store_slug, image_type, product_id_2)

        self.assertEqual(result_url,
            "http://imageservice.elasticbeanstalk.com/images/some-store/product/123/instagram/queuebyurl?sourceUrl=http://example.com/image.jpg"
        )
