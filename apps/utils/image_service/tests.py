from django.utils import unittest
from django.conf import settings

from apps.utils.image_service.api import queue_processing

class ImageServiceAPITests(unittest.TestCase):
    def setUp(self):
        pass

    def test_queue_processing(self):
        result_url = queue_processing(
            "http://farm9.staticflickr.com/8379/8456408563_643b2d30e0.jpg")
        self.assertIn(settings.IMAGE_SERVICE_STORE, result_url)

        result_url = queue_processing("blah")
        self.assertEqual(result_url, None)
